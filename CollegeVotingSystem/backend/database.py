# backend/database.py
import os
import sqlite3
import mysql.connector

# MySQL configuration from environment variables or default values
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "33060"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Dharsan@07")
DB_NAME = os.getenv("DB_NAME", "college_voting")
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "voting.sqlite3")


def _normalize_sql(query: str):
    return query.replace("%s", "?")


def _dict_factory(cursor, row):
    return {key: row[key] for key in [column[0] for column in cursor.description]}


def get_connection(include_db=True):
    """
    Try MySQL first, and fall back to SQLite for local development.
    """
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME if include_db else None,
            autocommit=True,
        )
        return conn
    except Exception:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

def init_db():
    """
    Try MySQL first and fall back to SQLite initialization.
    """
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            autocommit=True,
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        conn.close()
        print("MySQL available. Using MySQL database.")
        return _init_mysql_schema()
    except Exception as e:
        print(f"MySQL not available, using SQLite fallback: {e}")
        return _init_sqlite_schema()


def _init_mysql_schema():
    try:
        conn = get_connection(include_db=True)
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'voters'")
            result = cursor.fetchone()
            if not result:
                _execute_schema_file(conn)
            else:
                print("Database tables verified. Ready for operation.")
        conn.close()
        return True
    except Exception as e:
        print(f"Error initializing database tables: {e}")
        return False


def _init_sqlite_schema():
    try:
        conn = get_connection(include_db=True)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='voters'")
        result = cursor.fetchone()

        if not result:
            cursor.executescript('''
                CREATE TABLE voters (
                    voter_id TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    department TEXT NOT NULL
                );

                CREATE TABLE candidates (
                    candidate_id TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    degree TEXT NOT NULL,
                    qualification TEXT NOT NULL,
                    achievements TEXT NOT NULL,
                    manifesto TEXT NOT NULL,
                    image_url TEXT DEFAULT '',
                    position TEXT NOT NULL
                );

                CREATE TABLE votes (
                    voter_id TEXT NOT NULL,
                    position TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    vote_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (voter_id, position),
                    FOREIGN KEY (voter_id) REFERENCES voters(voter_id) ON DELETE CASCADE,
                    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE
                );

                DELETE FROM votes;
                DELETE FROM candidates;
                DELETE FROM voters;

                INSERT INTO voters (voter_id, password, name, department) VALUES
                ('STU001', 'password123', 'David Miller', 'Computer Science'),
                ('STU002', 'password123', 'Emily Watson', 'Electronics Engineering'),
                ('STU003', 'password123', 'Sanjay Kumar', 'Mechanical Engineering'),
                ('STU004', 'password123', 'Aisha Rahman', 'Bio-Technology'),
                ('STU005', 'password123', 'Carlos Garcia', 'Information Technology');

                INSERT INTO candidates (candidate_id, password, name, degree, qualification, achievements, manifesto, image_url, position) VALUES
                ('PRES01', 'pass123', 'Jonathan Hughes', 'B.Tech CS, 3rd Year', 'Class Representative, GPA 3.9', 'Organized the annual national college hackathon, lead organizer of the environment club, active debate society mentor.', 'I promise to advocate for 24/7 library access, upgrade computer lab infrastructures, and establish a transparent student budget tracker.', '', 'President'),
                ('PRES02', 'pass123', 'Priya Sharma', 'B.Sc Economics, 3rd Year', 'President of Debating Society, Sports Captain', 'Successfully petitioned for girls hostel security upgrades, organized corporate internship job fairs, represented college in national MUN.', 'My manifesto focuses on introducing mental wellness programs, campus-wide recycling, and establishing an entrepreneurial incubator cell.', '', 'President'),
                ('VP01', 'pass123', 'Marcus Aurelius', 'B.Tech IT, 2nd Year', 'Secretary of Robotics Club, Event Coordinator', 'Co-organized the tech-fest tech exhibition, designed the college companion mobile app, active sports council member.', 'I will push for digital student ID card integrations, expand campus Wi-Fi bandwidth, and host monthly micro-innovation challenges.', '', 'Vice President'),
                ('VP02', 'pass123', 'Sofia Rodriguez', 'B.Sc Mathematics, 2nd Year', 'General Secretary, Mathematics Association', 'Conducted peer-to-peer tutoring workshops for 1st-year students, coordinated inter-college math olympiad.', 'I pledge to secure subsidized student travel passes, increase funding for non-technical societies, and clean the sports arena.', '', 'Vice President'),
                ('SEC01', 'pass123', 'Liam Carter', 'B.Tech CS, 2nd Year', 'Core member of Web Development Cell', 'Designed the departmental newsletter website, active volunteer at open source development community.', 'I will coordinate weekly coding contests, push for student-mentor guidance programs, and organize guest lectures from tech leaders.', '', 'General Secretary'),
                ('SEC02', 'pass123', 'Neha Patel', 'B.Tech Biotech, 2nd Year', 'Class Coordinator, Cult-fest Organizer', 'Spearheaded department laboratory upgrades drive, organized cultural performances at the college foundation day.', 'I am dedicated to organizing regular industrial lab visits, expanding research seminar sessions, and bridging peer connection gaps.', '', 'General Secretary');
            ''')
            conn.commit()
            print("SQLite database initialized successfully with mock data!")
        else:
            print("SQLite tables verified. Ready for operation.")
        conn.close()
        return True
    except Exception as e:
        print(f"Error initializing SQLite tables: {e}")
        return False

def fetch_all(query, params=None):
    """
    Executes a SELECT query and returns all matching rows as a list of dictionaries.
    """
    conn = get_connection()
    try:
        if isinstance(conn, sqlite3.Connection):
            cursor = conn.cursor()
            cursor.execute(_normalize_sql(query), params or ())
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        with conn.cursor(dictionary=True) as cursor:
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
        if isinstance(conn, sqlite3.Connection):
            cursor = conn.cursor()
            cursor.execute(_normalize_sql(query), params or ())
            row = cursor.fetchone()
            return dict(row) if row else None
        with conn.cursor(dictionary=True) as cursor:
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
        if isinstance(conn, sqlite3.Connection):
            cursor = conn.cursor()
            cursor.execute(_normalize_sql(query), params or ())
            conn.commit()
            return cursor.rowcount
        with conn.cursor(dictionary=True) as cursor:
            result = cursor.execute(query, params or ())
            return result
    finally:
        conn.close()
