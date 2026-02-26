import sqlite3
import os

DB_FILE = os.path.join('data', 'history_events.db')
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute('SELECT sql FROM sqlite_master WHERE name="historical_events"')
print(cursor.fetchone()[0])

print("\n")
cursor.execute('PRAGMA table_info(historical_events)')
print("cid | name | type | notnull | dflt_value | pk")
for row in cursor.fetchall():
    print(" | ".join(str(x) for x in row))

conn.close()
