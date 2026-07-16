import database

print("=== VOTERS ===")
rows = database.fetch_all("SELECT * FROM voters")

for row in rows:
    print(row)