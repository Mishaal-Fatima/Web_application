import sqlite3
from prettytable import PrettyTable

# Connect to the SQLite database
conn = sqlite3.connect("robot_data.db")
cursor = conn.cursor()

# Fetch data from the table
cursor.execute("SELECT * FROM robot_data")
rows = cursor.fetchall()

# Close the connection
conn.close()

# Create a PrettyTable instance
table = PrettyTable()
table.field_names = ["ID", "Device ID", "State", "Time"]

# Add rows to the table
for row in rows:
    table.add_row(row)

# Print the table
print(table)
