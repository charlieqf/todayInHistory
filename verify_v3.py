import sqlite3
import os

DB_FILE = os.path.join('data', 'history_events.db')
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

print('--- Tables ---')
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
for row in cursor.fetchall():
    print(row[0])

print('\n--- Channels ---')
cursor.execute('SELECT count(*) FROM channels')
print(f'Channels count: {cursor.fetchone()[0]}')

print('\n--- Historical Events ---')
cursor.execute('SELECT count(*) FROM historical_events')
print(f'Events count: {cursor.fetchone()[0]}')

cursor.execute('PRAGMA table_info(historical_events)')
columns = cursor.fetchall()
is_month_nullable = any(row[1] == 'month' and row[3] == 0 for row in columns)
print(f'Is month nullable: {is_month_nullable}')

conn.close()
