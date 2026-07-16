# backend/database.py
import os
import sqlite3

try:
    import mysql.connector as mysql_connector
except ImportError:  # pragma: no cover - optional dependency for local fallback
    mysql_connector = None

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


def _get_mysql_connection(include_db=True):
    if mysql_connector is None:
        raise RuntimeError("mysql.connector is not installed")

    return mysql_connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME if include_db else None,
        autocommit=True,
    )


def get_connection(include_db=True):
    """
    Try MySQL first, and fall back to SQLite for local development.
    """
    try:
        return _get_mysql_connection(include_db=include_db)
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
        conn = _get_mysql_connection(include_db=False)
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
        conn = _get_mysql_connection(include_db=True)
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS voters (
                    voter_id VARCHAR(50) PRIMARY KEY,
                    password VARCHAR(255) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    department VARCHAR(100) NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS election_settings (
                    id INTEGER PRIMARY KEY,
                    election_status VARCHAR(20) NOT NULL
                )
                """
            )
            cursor.execute(
                """
                INSERT IGNORE INTO election_settings (id, election_status)
                VALUES (1, 'STOPPED')
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS candidates (
                    candidate_id VARCHAR(50) PRIMARY KEY,
                    password VARCHAR(255) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    degree VARCHAR(100) NOT NULL,
                    qualification VARCHAR(255) NOT NULL,
                    achievements TEXT NOT NULL,
                    manifesto TEXT NOT NULL,
                    image_url VARCHAR(255) DEFAULT '',
                    position VARCHAR(50) NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS votes (
                    voter_id VARCHAR(50) NOT NULL,
                    position VARCHAR(50) NOT NULL,
                    candidate_id VARCHAR(50) NOT NULL,
                    vote_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (voter_id, position),
                    FOREIGN KEY (voter_id) REFERENCES voters(voter_id) ON DELETE CASCADE,
                    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE
                )
                """
            )
            cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS election_settings (
        id INT PRIMARY KEY,
        election_status VARCHAR(20) NOT NULL
    )
    """
)
        conn.close()
        print("MySQL tables verified. Ready for operation.")
        return True
    except Exception as e:
        print(f"Error initializing MySQL tables: {e}")
        return False


def _init_sqlite_schema():
    try:
        conn = get_connection(include_db=True)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='voters'")
        result = cursor.fetchone()

        if not result:
            cursor.executescript(
                """
                CREATE TABLE voters (
                    voter_id TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    department TEXT NOT NULL
                );
                
                CREATE TABLE election_settings (
                    id INTEGER PRIMARY KEY,
                    election_status TEXT NOT NULL
                    );
                    
                    INSERT INTO election_settings (id, election_status)
                    VALUES (1, 'STOPPED');

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
                CREATE TABLE election_settings (
    id INTEGER PRIMARY KEY,
    election_status TEXT NOT NULL
);

                CREATE TABLE election_settings (
                    id INTEGER PRIMARY KEY,
                    election_status TEXT NOT NULL
                );
                """
            )

            cursor.execute("SELECT COUNT(*) FROM voters")
            if cursor.fetchone()[0] == 0:
                cursor.executescript(
                    """
                    INSERT INTO voters (voter_id, password, name, department) VALUES
                    ('24AD001', '123456', 'Dharsan S', 'Artificial Intelligence & Data Science'),
                    ('24AD002', '123456', 'Arun Kumar', 'Artificial Intelligence & Data Science'),
                    ('24AD003', '123456', 'Kavin Raj', 'Artificial Intelligence & Data Science'),
                    ('24CS001', '123456', 'Praveen Kumar', 'Computer Science'),
                    ('24EC001', '123456', 'Harish Kumar', 'Electronics and Communication');

                    INSERT INTO candidates (candidate_id, password, name, degree, qualification, achievements, manifesto, image_url, position) VALUES
                    ('PRES01', '123456', 'Dharsan S', 'B.Tech AI & DS - II Year', 'Class Representative', 'Organized technical events and actively participated in coding competitions.', 'I will improve student facilities, encourage innovation, and make student voices heard.', '', 'President'),
                    ('PRES02', '123456', 'Gowtham Kowsik', 'B.Tech AI & DS - II Year', 'NSS Volunteer', 'Successfully coordinated college events and community service activities.', 'I will strengthen communication between students and management and support extracurricular activities.', '', 'President'),
                    ('VP01', '123456', 'Arun Kumar', 'B.Tech AI & DS - II Year', 'Technical Club Member', 'Developed student mini projects and participated in hackathons.', 'I will improve technical workshops and provide more placement training opportunities.', '', 'Vice President'),
                    ('VP02', '123456', 'Kavin Raj', 'B.Tech AI & DS - II Year', 'Sports Coordinator', 'Led department sports activities and organized tournaments.', 'I will promote sports, cultural events, and student well-being.', '', 'Vice President'),
                    ('SEC01', '123456', 'Praveen Kumar', 'B.Tech Computer Science - II Year', 'Coding Club Secretary', 'Conducted programming workshops and coding contests.', 'I will organize regular coding events and improve technical knowledge sharing.', '', 'General Secretary'),
                    ('SEC02', '123456', 'Harish Kumar', 'B.E ECE - II Year', 'IEEE Student Member', 'Organized electronics workshops and technical seminars.', 'I will encourage research activities and strengthen department collaboration.', '', 'General Secretary');
                    """
                )
                cursor.execute(
    """
    INSERT OR IGNORE INTO election_settings
    (id, election_status)
    VALUES (1, 'STOPPED')
    """
)

            conn.commit()
            print("SQLite database initialized successfully with mock data!")
        else:
            print("SQLite tables verified. Ready for operation.")

        # Ensure election_settings table exists and has a default row
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS election_settings (
                    id INTEGER PRIMARY KEY,
                    election_status TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                "INSERT OR IGNORE INTO election_settings (id, election_status) VALUES (1, 'STOPPED')"
            )
            conn.commit()
        except Exception:
            pass

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
            cursor.execute(query, params or ())
            return cursor.rowcount
    finally:
        conn.close()
def executemany_query(query, data):
    """
    Executes the same query for multiple rows.
    Used for CSV student upload.
    """
    conn = get_connection()
    try:
        if isinstance(conn, sqlite3.Connection):
            cursor = conn.cursor()
            cursor.executemany(_normalize_sql(query), data)
            conn.commit()
            return cursor.rowcount
        else:
            with conn.cursor() as cursor:
                cursor.executemany(query, data)
            conn.commit()
            return cursor.rowcount
    finally:
        conn.close()