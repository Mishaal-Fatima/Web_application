import sqlite3

# Create SQLite database and table
conn = sqlite3.connect("robot_data.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE robot_data (id INTEGER PRIMARY KEY AUTOINCREMENT, device_id TEXT, state TEXT, time TEXT)")
conn.commit()

# Close the connection
conn.close()