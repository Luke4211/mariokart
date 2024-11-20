import sqlite3
import csv

# Configuration
DATABASE = 'mariokart.db'
TABLE_NAME = 'luke_liam'
CSV_FILE = 'initial.csv'

# Drop and recreate the table, then load data from CSV
def reload_table():
    # Connect to the database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Drop the table if it exists
    cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")

    # Recreate the table
    cursor.execute(f"""
        CREATE TABLE {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Map TEXT NOT NULL,
            Score INTEGER NOT NULL
        );
    """)

    print(f"Table '{TABLE_NAME}' recreated.")

    # Read data from the CSV file
    with open(CSV_FILE, 'r') as csv_file:
        reader = csv.reader(csv_file)
        rows = [(row[0], int(row[1])) for row in reader]  # Auto-generate ID

    # Insert data into the table
    cursor.executemany(f"""
        INSERT INTO {TABLE_NAME} (Map, Score)
        VALUES (?, ?);
    """, rows)

    print(f"Data loaded from '{CSV_FILE}' into '{TABLE_NAME}'.")

    # Commit changes and close the connection
    conn.commit()
    conn.close()

if __name__ == '__main__':
    reload_table()
