import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import bcrypt
import logging

load_dotenv()

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
        logging.info(f"Verifying user: {username}")
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
                SELECT p.*, u.username as author_name, s.name as subreddit_name,
                    (SELECT COUNT(*) FROM votes WHERE post_id = p.id AND vote_type = 1) as upvotes,
                    (SELECT COUNT(*) FROM votes WHERE post_id = p.id AND vote_type = -1) as downvotes
                FROM posts p
                JOIN users u ON p.author = u.username
                JOIN subreddits s ON p.subreddit_id = s.id
                WHERE p.subreddit_id = %s
                ORDER BY p.created_at DESC
            """
            cursor.execute(sql, (subreddit_id,))
        else:
            sql = """
                SELECT p.*, u.username as author_name, s.name as subreddit_name,
                    (SELECT COUNT(*) FROM votes WHERE post_id = p.id AND vote_type = 1) as upvotes,
                    (SELECT COUNT(*) FROM votes WHERE post_id = p.id AND vote_type = -1) as downvotes
                FROM posts p
                JOIN users u ON p.author = u.username
                JOIN subreddits s ON p.subreddit_id = s.id
                ORDER BY p.created_at DESC
            """
            cursor.execute(sql)
        return cursor.fetchall()
    except Error as e:
        print(f"Error: {e}")
        return []
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
            SELECT c.*, u.username as author_name
            FROM comments c
            JOIN users u ON c.author = u.username
            WHERE c.post_id = %s
            ORDER BY c.created_at DESC
        """
        cursor.execute(sql, (post_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# Vote operations
def vote_post(post_id, username, vote_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # First try to update existing vote
        sql = """
            INSERT INTO votes (post_id, username, vote_type)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE vote_type = %s
        """
        cursor.execute(sql, (post_id, username, vote_type, vote_type))
        conn.commit()
        return True
    except Error as e:
        print(f"Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()