
import sqlite3
import csv
import os


# Configuration
DATABASE = 'mariokart.db'
TABLE_NAME = 'luke_liam'
DEFAULT_TIMESTAMP = '2024-11-13 00:00:00'  # Default timestamp value

# Locate the most recent file in the /archive directory
ARCHIVE_DIR = os.path.join(os.getcwd(), 'archive')


# Find the most recent file in the archive directory
def get_most_recent_file(directory):
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.csv')]
    if not files:
        raise FileNotFoundError(f"No CSV files found in the archive directory: {directory}")
    return max(files, key=os.path.getmtime)


CSV_FILE = get_most_recent_file(ARCHIVE_DIR)
print(f"Most recent CSV file selected: {CSV_FILE}")


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
            Player1_Score INTEGER,
            Player2_Score INTEGER,
            Score INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        );
    """)

    print(f"Table '{TABLE_NAME}' recreated.")

    # Read data from the CSV file
    with open(CSV_FILE, 'r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader, None)
        rows = []
        for row in reader:
            # Exclude the ID column (row[0]) and adjust the mapping
            map_id = row[1]  # Map column
            player1_score = int(row[2]) if row[2].strip() else None
            player2_score = int(row[3]) if row[3].strip() else None
            score = int(row[4])  # Combined Score
            timestamp = row[5] if len(row) > 5 and row[5].strip() else DEFAULT_TIMESTAMP

            rows.append((map_id, player1_score, player2_score, score, timestamp))

    # Insert data into the table
    cursor.executemany(f"""
        INSERT INTO {TABLE_NAME} (Map, Player1_Score, Player2_Score, Score, timestamp)
        VALUES (?, ?, ?, ?, ?);
    """, rows)

    print(f"Data loaded from '{CSV_FILE}' into '{TABLE_NAME}'.")

    # Commit changes and close the connection
    conn.commit()
    conn.close()


if __name__ == '__main__': 
    reload_table()