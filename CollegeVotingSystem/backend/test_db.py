import os

try:
    import mysql.connector as mysql_connector
except Exception as exc:  # pragma: no cover - safety for missing package
    mysql_connector = None
    print("mysql.connector import failed:", exc)

if mysql_connector is None:
    print("mysql.connector is unavailable; skipping connection probe.")
else:
    try:
        conn = mysql_connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            autocommit=True,
        )
        print("CONNECTION_OK")
        conn.close()
    except Exception as exc:
        import traceback
        traceback.print_exc()
        print("CONNECTION_FAIL", repr(exc))
