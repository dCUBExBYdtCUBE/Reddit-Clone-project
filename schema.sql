-- Create the database (if not already created)
DROP DATABASE IF EXISTS reddit_clone;
CREATE DATABASE IF NOT EXISTS reddit_clone;
USE reddit_clone;

-- Create the users table
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the subreddits table
CREATE TABLE subreddits (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) UNIQUE NOT NULL,
  description TEXT,
  creator VARCHAR(50) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (creator) REFERENCES users(username) ON DELETE CASCADE
);

-- Create the posts table
CREATE TABLE posts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(300) NOT NULL,
  content TEXT NOT NULL,
  author VARCHAR(50) NOT NULL,
  subreddit_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (author) REFERENCES users(username) ON DELETE CASCADE,
  FOREIGN KEY (subreddit_id) REFERENCES subreddits(id) ON DELETE CASCADE
);

-- Create the comments table
CREATE TABLE comments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  content TEXT NOT NULL,
  author VARCHAR(50) NOT NULL,
  post_id INT NOT NULL,
  parent_id INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (author) REFERENCES users(username) ON DELETE CASCADE,
  FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

-- Create the moderators table
CREATE TABLE moderators (
  id INT AUTO_INCREMENT PRIMARY KEY,
  subreddit_id INT NOT NULL,
  username VARCHAR(50) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (subreddit_id) REFERENCES subreddits(id) ON DELETE CASCADE,
  FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

-- Create the votes table (updated for both posts and comments)
CREATE TABLE votes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  post_id INT,
  comment_id INT,
  username VARCHAR(50) NOT NULL,
  vote_type TINYINT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
  FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE,
  FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
  CHECK (post_id IS NOT NULL OR comment_id IS NOT NULL),  -- Ensure one of the two is not NULL
  CHECK (NOT (post_id IS NOT NULL AND comment_id IS NOT NULL))  -- Prevent both from being non-NULL
);

-- Procedure(s)

drop procedure if exists vote_item;

DELIMITER //

CREATE PROCEDURE vote_item(
    IN item_id INT,
    IN username VARCHAR(255),
    IN vote_type TINYINT,
    IN item_type ENUM('post', 'comment')
)
BEGIN
    DECLARE current_vote TINYINT;

    IF item_type = 'post' THEN
        SELECT vote_type INTO current_vote
        FROM votes
        WHERE post_id = item_id AND username = username;

        IF current_vote IS NULL THEN
            INSERT INTO votes (post_id, username, vote_type)
            VALUES (item_id, username, vote_type);
        ELSEIF current_vote = vote_type THEN
            DELETE FROM votes
            WHERE post_id = item_id AND username = username;
        ELSE
            UPDATE votes
            SET vote_type = vote_type
            WHERE post_id = item_id AND username = username;
        END IF;
    ELSEIF item_type = 'comment' THEN
        SELECT vote_type INTO current_vote
        FROM votes
        WHERE comment_id = item_id AND username = username;

        IF current_vote IS NULL THEN
            INSERT INTO votes (comment_id, username, vote_type)
            VALUES (item_id, username, vote_type);
        ELSEIF current_vote = vote_type THEN
            DELETE FROM votes
            WHERE comment_id = item_id AND username = username;
        ELSE
            UPDATE votes
            SET vote_type = vote_type
            WHERE comment_id = item_id AND username = username;
        END IF;
    ELSE
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Invalid item_type';
    END IF;
END //

DELIMITER ;

-- Trigger(s)

DELIMITER //

CREATE TRIGGER after_subreddit_insert
AFTER INSERT ON subreddits
FOR EACH ROW
BEGIN
    -- Insert the subreddit creator into the moderators table
    INSERT INTO moderators (subreddit_id, username)
    VALUES (NEW.id, NEW.creator);
END//

DELIMITER ;
