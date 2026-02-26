import sqlite3
import os

DB_FILE = os.path.join('data', 'history_events.db')
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute('''
    SELECT title, count(*) 
    FROM historical_events 
    GROUP BY title 
    HAVING count(*) > 1
''')

print("Duplicate Titles Found:")
for row in cursor.fetchall():
    print(f"'{row[0]}' appears {row[1]} times")

conn.close()
