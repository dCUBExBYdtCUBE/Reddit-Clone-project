import streamlit as st
import database as db
import logging

logging.basicConfig(
    level=logging.INFO,  # Set level to INFO
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    handlers=[
        logging.StreamHandler()  # Ensure logs are shown in the console
    ]
)

def init_session_state():
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_subreddit' not in st.session_state:
        st.session_state.current_subreddit = None

def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            user = db.verify_user(username, password)
            logging.info(f"User: {user}")
            if user!= None:
                st.session_state.user = user
                st.success("Logged in successfully!")
                logging.info(f"User: {st.session_state.user}")
                st.session_state.page = "home"
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")
                logging.error("Invalid credentials")
    
    with col2:
        if st.button("Register"):
            st.session_state.page = "register"
            st.experimental_rerun()

def register_page():
    st.title("Register")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Create Account"):
        if password != confirm_password:
            st.error("Passwords don't match")
        else:
            try:
                if db.create_user(username, password, email):
                    st.success("Account created successfully!")
                    st.session_state.page = "login"
                    st.experimental_rerun()
                else:
                    st.error("Error creating account")
            except Exception as e:
                st.error(f"Error creating account: {str(e)}")

def create_subreddit_page():
    if not st.session_state.user:
        st.error("You must be logged in to create a subreddit.")
        return

    st.title("Create Subreddit")
    st.write("Log: Rendering input fields for subreddit creation.")
    name = st.text_input("Subreddit Name")
    description = st.text_area("Description")

    if st.button("Create Subreddit"):
        st.write("Log: 'Create Subreddit' button clicked.")
        success = db.create_subreddit(name, description, st.session_state.user['username'])
        if success:
            st.success("Subreddit created successfully!")
            st.session_state.page = "home"
            st.experimental_rerun()
        else:
            st.error("Error creating subreddit")

def create_post_page():
    st.title("Create Post")
    subreddits = db.get_subreddits()
    subreddit_names = {s['id']: s['name'] for s in subreddits}
    selected_subreddit = st.selectbox("Select Subreddit", options=list(subreddit_names.keys()), format_func=lambda x: subreddit_names[x])
    
    title = st.text_input("Title")
    content = st.text_area("Content")

    if st.button("Create Post"):
        if db.create_post(title, content, st.session_state.user['username'], selected_subreddit):
            st.success("Post created successfully!")
            st.session_state.page = "home"
            st.experimental_rerun()
        else:
            st.error("Error creating post")

def display_post(post):
    st.markdown(f"### {post['title']}")
    st.markdown(f"Posted by u/{post['author_name']} in r/{post['subreddit_name']}")
    st.markdown(post['content'])

    col1, col2, col3 = st.columns([1, 1, 8])
    with col1:
        if st.button("⬆️", key=f"up_{post['id']}"):
            if st.session_state.user:
                db.vote_post(post['id'], st.session_state.user['username'], 1)
                st.experimental_rerun()
            else:
                st.error("Please login to vote")

    with col2:
        if st.button("⬇️", key=f"down_{post['id']}"):
            if st.session_state.user:
                db.vote_post(post['id'], st.session_state.user['username'], -1)
                st.experimental_rerun()
            else:
                st.error("Please login to vote")

    st.markdown(f"Score: {post['upvotes'] - post['downvotes']}")

    # Delete button for the post if the user is the creator
    if st.session_state.user and st.session_state.user['username'] == post['subreddit_creator']:
        if st.button("🗑️ Delete Post", key=f"delete_post_{post['id']}"):
            if db.delete_post(post['id'], post['subreddit_id'], st.session_state.user['username']):
                st.success("Post deleted successfully.")
                st.experimental_rerun()
            else:
                st.error("Error deleting post.")

    # Comments
    comments = db.get_comments(post['id'])
    if st.session_state.user:
        comment_text = st.text_area("Add a comment", key=f"comment_{post['id']}")
        if st.button("Submit Comment", key=f"submit_comment_{post['id']}"):
            if db.create_comment(comment_text, st.session_state.user['username'], post['id']):
                st.success("Comment added successfully!")
                st.experimental_rerun()
            else:
                st.error("Error adding comment")

    for comment in comments:
        col1, col2, col3 = st.columns([1, 1, 8])
        with col1:
            if st.button("⬆️", key=f"up_comment_{comment['id']}"):
                if st.session_state.user:
                    db.vote_item(comment['id'], st.session_state.user['username'], 1, item_type='comment')
                    st.experimental_rerun()
                else:
                    st.error("Please login to vote")
        with col2:
            if st.button("⬇️", key=f"down_comment_{comment['id']}"):
                if st.session_state.user:
                    db.vote_item(comment['id'], st.session_state.user['username'], -1, item_type='comment')
                    st.experimental_rerun()
                else:
                    st.error("Please login to vote")

        st.markdown(f"Score: {comment['upvotes'] - comment['downvotes']}")
        st.markdown(f"> **{comment['author_name']}**: {comment['content']}")

        # Delete button for the comment if the user is the creator
        if st.session_state.user and st.session_state.user['username'] == post['subreddit_creator']:
            if st.button("🗑️ Delete Comment", key=f"delete_comment_{comment['id']}"):
                if db.delete_comment(comment['id'], post['id'], st.session_state.user['username']):
                    st.success("Comment deleted successfully.")
                    st.experimental_rerun()
                else:
                    st.error("Error deleting comment.")


def home_page():
    st.title("Reddit Clone")
    
    # Sidebar
    with st.sidebar:
        if st.session_state.user:
            st.write(f"Welcome, {st.session_state.user['username']}!")
            if st.button("Create Subreddit"):
                st.session_state.page = "create_subreddit"
                st.experimental_rerun()
            if st.button("Create Post"):
                st.session_state.page = "create_post"
                st.experimental_rerun()
            if st.button("Logout"):
                st.session_state.user = None
                st.experimental_rerun()
        else:
            if st.button("Login"):
                st.session_state.page = "login"
                st.experimental_rerun()

        # Subreddit list
        st.markdown("### Subreddits")
        subreddits = db.get_subreddits()
        for subreddit in subreddits:
            if st.button(f"r/{subreddit['name']}", key=subreddit['id']):
                st.session_state.current_subreddit = subreddit['id']
                st.experimental_rerun()

    # Main content
    posts = db.get_posts(st.session_state.current_subreddit)
    for post in posts:
        display_post(post)
        st.markdown("---")

def main():
    init_session_state()
    
    if 'page' not in st.session_state:
        st.session_state.page = "home"

    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "register":
        register_page()
    elif st.session_state.page == "create_subreddit":
        create_subreddit_page()
    elif st.session_state.page == "create_post":
        create_post_page()
    else:
        home_page()

if __name__ == "__main__":
    main()
