import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import bcrypt
import logging

load_dotenv()

# Get DB connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Password hashing and checking
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# User operations
def create_user(username, password, email):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        hashed_password = hash_password(password).decode('utf-8')
        sql = "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, hashed_password, email))
        conn.commit()
        return True
    except Error as e:
        logging.error(f"Error creating user: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def verify_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    logging.info(f"Verifying user: {username}")
    try:
        sql = "SELECT id, username, password FROM users WHERE username = %s"
        cursor.execute(sql, (username,))
        user = cursor.fetchone()
        if user and check_password(password, user['password']):
            logging.info(f"User {username} verified successfully")
            return {'id': user['id'], 'username': user['username']}
        return None
    except Error as e:
        logging.error(f"Error verifying user: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

# Subreddit operations
def create_subreddit(name, description, creator):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO subreddits (name, description, creator) VALUES (%s, %s, %s)"
        cursor.execute(sql, (name, description, creator))
        conn.commit()
        return True
    except Error as e:
        print(f"Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_subreddits():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        sql = "SELECT * FROM subreddits ORDER BY created_at DESC"
        cursor.execute(sql)
        return cursor.fetchall()
    except Error as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# Post operations
def create_post(title, content, author, subreddit_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO posts (title, content, author, subreddit_id) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (title, content, author, subreddit_id))
        conn.commit()
        return True
    except Error as e:
        print(f"Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_posts(subreddit_id=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if subreddit_id:
            sql = """
                SELECT p.*, u.username as author_name, s.name as subreddit_name
                FROM posts p
                JOIN users u ON p.author = u.username
                JOIN subreddits s ON p.subreddit_id = s.id
                WHERE p.subreddit_id = %s
                ORDER BY p.created_at DESC
            """
            cursor.execute(sql, (subreddit_id,))
            posts = cursor.fetchall()

            for post in posts:
                post['upvotes'], post['downvotes'] = get_post_vote_counts(post['id'])

        else:
            sql = """
                SELECT p.*, u.username as author_name, s.name as subreddit_name
                FROM posts p
                JOIN users u ON p.author = u.username
                JOIN subreddits s ON p.subreddit_id = s.id
                ORDER BY p.created_at DESC
            """
            cursor.execute(sql)
            posts = cursor.fetchall()

            for post in posts:
                post['upvotes'], post['downvotes'] = get_post_vote_counts(post['id'])

        return posts
    except Error as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_post_vote_counts(post_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get count of upvotes and downvotes directly from the database
        sql_upvotes = "SELECT COUNT(*) FROM votes WHERE post_id = %s AND vote_type = 1"
        sql_downvotes = "SELECT COUNT(*) FROM votes WHERE post_id = %s AND vote_type = -1"
        
        cursor.execute(sql_upvotes, (post_id,))
        upvotes = cursor.fetchone()[0]  # Fetch the count of upvotes
        
        cursor.execute(sql_downvotes, (post_id,))
        downvotes = cursor.fetchone()[0]  # Fetch the count of downvotes

        return upvotes, downvotes
    except Error as e:
        print(f"Error: {e}")
        return 0, 0
    finally:
        cursor.close()
        conn.close()

# Comment operations
def create_comment(content, author, post_id, parent_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO comments (content, author, post_id, parent_id) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (content, author, post_id, parent_id))
        conn.commit()
        return True
    except Error as e:
        print(f"Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_comments(post_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        sql = """
            SELECT c.id, c.content, c.author, c.post_id, c.parent_id, c.created_at,
                u.username as author_name,
                (SELECT COUNT(*) FROM votes WHERE comment_id = c.id AND vote_type = 1) as upvotes,
                (SELECT COUNT(*) FROM votes WHERE comment_id = c.id AND vote_type = -1) as downvotes
            FROM comments c
            JOIN users u ON c.author = u.username
            WHERE c.post_id = %s
            ORDER BY c.created_at DESC
        """
        cursor.execute(sql, (post_id,))
        comments = cursor.fetchall()
        return comments
    except Error as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def vote_post(post_id, username, vote_type):
    """
    Function to vote on a post.

    Parameters:
    - post_id: ID of the post.
    - username: The username of the person voting.
    - vote_type: The type of vote (e.g., upvote/downvote).

    Returns:
    - True if the vote was successful, False otherwise.
    """
    return vote_item(post_id, username, vote_type, item_type='post')

def vote_item(item_id, username, vote_type, item_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.callproc('vote_item', (item_id, username, vote_type, item_type))
        conn.commit()
        return True
    except Error as e:
        print(f"Error: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
