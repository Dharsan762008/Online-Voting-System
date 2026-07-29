# backend/database.py
import os
import urllib.parse
import pymysql
import pymysql.cursors

# MySQL configuration from environment variables or default values
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Parse e.g., mysql://user:password@host:port/dbname
    parsed = urllib.parse.urlparse(DATABASE_URL)
    DB_HOST = parsed.hostname
    DB_USER = parsed.username
    DB_PASSWORD = parsed.password or ""
    DB_NAME = parsed.path.lstrip("/")
    DB_PORT = parsed.port or 3306
else:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "college_voting")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))

def get_connection(include_db=True):
    """
    Establishes a connection to the MySQL server.
    """
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        database=DB_NAME if include_db else None,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def init_db():
    """
    Checks if database and tables exist. If not, creates them using schema.sql.
    """
    # 1. First, connect without specifying a DB to create the database if it doesn't exist
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            autocommit=True
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        conn.close()
    except Exception as e:
        print(f"Error connecting to MySQL server to check/create database: {e}")
        print("Please ensure your MySQL service is running and credentials are correct.")
        return False

    # 2. Connect to the database and check if tables are created
    try:
        conn = get_connection(include_db=True)
        with conn.cursor() as cursor:
            # Check if voters table exists as a proxy for the schema
            cursor.execute("SHOW TABLES LIKE 'voters'")
            result = cursor.fetchone()
            
            if not result:
                print("Database tables not found. Initializing schema from schema.sql...")
                schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schema.sql")
                if os.path.exists(schema_path):
                    with open(schema_path, "r", encoding="utf-8") as f:
                        schema_sql = f.read()
                    
                    # Split queries by semicolon and execute (handling comments and whitespace)
                    # We strip off empty items
                    queries = schema_sql.split(";")
                    for query in queries:
                        clean_query = query.strip()
                        # Skip empty queries or queries that are just SQL comments
                        if clean_query and not clean_query.startswith("--"):
                            cursor.execute(clean_query)
                    print("Database initialized successfully with mock data!")
                else:
                    print("Warning: schema.sql file not found in root directory. Cannot auto-initialize tables.")
            else:
                print("Database tables verified. Ready for operation.")
        conn.close()
        return True
    except Exception as e:
        print(f"Error initializing database tables: {e}")
        return False

def fetch_all(query, params=None):
    """
    Executes a SELECT query and returns all matching rows as a list of dictionaries.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
    finally:
        conn.close()

def fetch_one(query, params=None):
    """
    Executes a SELECT query and returns a single row as a dictionary (or None).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()
    finally:
        conn.close()

def execute_query(query, params=None):
    """
    Executes an INSERT, UPDATE, or DELETE query and returns the number of affected rows.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            return cursor.execute(query, params or ())
    finally:
        conn.close()
