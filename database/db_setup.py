import sqlite3

connection = sqlite3.connect('mariokart.db')

with connection:
    connection.execute('''
        CREATE TABLE IF NOT EXISTS luke_liam (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Map TEXT NOT NULL,
            Score INTEGER NOT NULL
        )
    ''')

print("Database setup complete.")
