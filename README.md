# Reddit Clone Project

A simple **Reddit clone** built as a **Database Management Systems (DBMS) project** using **Python**, **Streamlit**, and **MySQL**.

![Built with Python](https://img.shields.io/badge/Built%20with-Python-blue)
![Streamlit App](https://img.shields.io/badge/Framework-Streamlit-orange)
![Database-MySQL](https://img.shields.io/badge/Database-MySQL-blue)

---

## 📚 Features
- User authentication (login/signup)
- Create posts
- Upvote and downvote posts
- Comment system
- Simple and clean UI with Streamlit

---

## 🚀 Getting Started

### 1. Set up the Database
- Run the `schema.sql` file to create the database and tables.

### 2. Configure Environment Variables
- Create a `.env` file in the project root directory and add the following details:

  ```
  DB_HOST=localhost
  DB_USER=your_username
  DB_PASSWORD=your_password
  DB_NAME=reddit_clone
  ```

  Replace `your_username` and `your_password` with your MySQL credentials.

### 3. Install Dependencies
- Install the required Python packages:

  ```bash
  pip install -r requirements.txt
  ```

### 4. Start the Application
- Run the app using Streamlit:

  ```bash
  streamlit run app.py
  ```

---

## 🛠 Tech Stack
- **Frontend:** Streamlit
- **Backend:** Python
- **Database:** MySQL

---
