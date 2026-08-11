# backend/database.py
import os
import sqlite3

try:
    import mysql.connector as mysql_connector
except ImportError:  # pragma: no cover - optional dependency for local fallback
    mysql_connector = None

# MySQL configuration from environment variables or default values.
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "college_voting")
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "voting.sqlite3")


def _normalize_sql(query: str):
    return query.replace("%s", "?")


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
    """Try MySQL first and fall back to SQLite for local development."""
    try:
        return _get_mysql_connection(include_db=include_db)
    except Exception:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def init_db():
    """Create the database schema if needed, using a SQLite fallback when MySQL is unavailable."""
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


def _execute_schema_file(conn):
    schema_path = os.path.join(os.path.dirname(__file__), "..", "schema.sql")
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as handle:
        statements = [statement.strip() for statement in handle.read().split(";") if statement.strip()]

    if isinstance(conn, sqlite3.Connection):
        conn.executescript(";".join(statements) + ";")
        conn.commit()
        return

    with conn.cursor() as cursor:
        for statement in statements:
            statement = statement.strip()
            if not statement or statement.startswith("--"):
                continue
            cursor.execute(statement)
    conn.commit()


def _init_mysql_schema():
    try:
        conn = get_connection(include_db=True)
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'voters'")
            if not cursor.fetchone():
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
            cursor.executescript(
                """
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

                CREATE TABLE election_settings (
                    id INTEGER PRIMARY KEY,
                    election_status TEXT NOT NULL
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
                ('PRES01', 'pass123', 'Dhanush M', 'B.Tech CS, 3rd Year', 'Class Representative, GPA 3.9', 'Organized the annual national college hackathon, lead organizer of the environment club, active debate society mentor.', 'I promise to advocate for 24/7 library access, upgrade computer lab infrastructures, and establish a transparent student budget tracker.', '', 'President'),
                ('PRES02', 'pass123', 'Dharsan S', 'B.Sc Economics, 3rd Year', 'President of Debating Society, Sports Captain', 'Successfully petitioned for girls hostel security upgrades, organized corporate internship job fairs, represented college in national MUN.', 'My manifesto focuses on introducing mental wellness programs, campus-wide recycling, and establishing an entrepreneurial incubator cell.', '', 'President'),
                ('VP01', 'pass123', 'Bharath M', 'B.Tech IT, 2nd Year', 'Secretary of Robotics Club, Event Coordinator', 'Co-organized the tech-fest tech exhibition, designed the college companion mobile app, active sports council member.', 'I will push for digital student ID card integrations, expand campus Wi-Fi bandwidth, and host monthly micro-innovation challenges.', '', 'Vice President'),
                ('VP02', 'pass123', 'Balaji G', 'B.Sc Mathematics, 2nd Year', 'General Secretary, Mathematics Association', 'Conducted peer-to-peer tutoring workshops for 1st-year students, coordinated inter-college math olympiad.', 'I pledge to secure subsidized student travel passes, increase funding for non-technical societies, and clean the sports arena.', '', 'Vice President'),
                ('SEC01', 'pass123', 'Claudius R', 'B.Tech CS, 2nd Year', 'Core member of Web Development Cell', 'Designed the departmental newsletter website, active volunteer at open source development community.', 'I will coordinate weekly coding contests, push for student-mentor guidance programs, and organize guest lectures from tech leaders.', '', 'General Secretary'),
                ('SEC02', 'pass123', 'Aravindh', 'B.Tech Biotech, 2nd Year', 'Class Coordinator, Cult-fest Organizer', 'Spearheaded department laboratory upgrades drive, organized cultural performances at the college foundation day.', 'I am dedicated to organizing regular industrial lab visits, expanding research seminar sessions, and bridging peer connection gaps.', '', 'General Secretary');

                INSERT OR IGNORE INTO election_settings (id, election_status) VALUES (1, 'STOPPED');
                """
            )
            conn.commit()
            print("SQLite database initialized successfully with mock data!")
        else:
            print("SQLite tables verified. Ready for operation.")

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS election_settings (id INTEGER PRIMARY KEY, election_status TEXT NOT NULL)"
        )
        cursor.execute("INSERT OR IGNORE INTO election_settings (id, election_status) VALUES (1, 'STOPPED')")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error initializing SQLite tables: {e}")
        return False


def fetch_all(query, params=None):
    """Execute a SELECT query and return all matching rows as dictionaries."""
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
    """Execute a SELECT query and return a single row as a dictionary or None."""
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
    """Execute an INSERT, UPDATE, or DELETE query."""
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
