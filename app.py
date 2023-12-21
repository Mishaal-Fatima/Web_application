from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

@app.route('/')
def index():
    # Connect to the SQLite database
    conn = sqlite3.connect("robot_data.db")
    cursor = conn.cursor()

    # Fetch the last updated value from the table
    cursor.execute("SELECT MAX(time) FROM robot_data")
    last_updated = cursor.fetchone()[0]

    # Fetch the latest 10 rows from the table
    cursor.execute(
        "SELECT ID, device_id, state, strftime('%Y-%m-%d %H:%M:%S', time) "
        "FROM robot_data ORDER BY time DESC LIMIT 10"
    )
    latest_rows = cursor.fetchall()

    # Fetch all data from the table (for the "Show All" option)
    cursor.execute(
        "SELECT ID, device_id, state, strftime('%Y-%m-%d %H:%M:%S', time) "
        "FROM robot_data ORDER BY time DESC"
    )
    all_rows = cursor.fetchall()

    # Close the connection
    conn.close()

    # Pass the data, last updated value, and latest rows to the template
    return render_template('dashboard.html', data=all_rows, last_updated=last_updated, latest_rows=latest_rows)

# Route for fetching robot data
@app.route('/get_robot_status', methods=['GET'])
def get_robot_status():
    robot_id = request.args.get('deviceId')
    print(f"Received request for device ID {robot_id}")

    # Connect to the SQLite database
    conn = sqlite3.connect("robot_data.db")
    cursor = conn.cursor()

    # Fetch status and timestamp for the specified robot ID
    #cursor.execute("SELECT state, time FROM robot_data WHERE device_id=?", (robot_id,))
    #cursor.execute("SELECT state, time FROM robot_data WHERE device_id=? ORDER BY time DESC LIMIT 1;", (robot_id,))
    cursor.execute("SELECT state, strftime('%Y-%m-%d %H:%M:%S', time) FROM robot_data WHERE device_id=? ORDER BY time DESC LIMIT 1",(robot_id,))

    row = cursor.fetchone()

    # Close the connection
    conn.close()

    print("row: ", row)

    # Return data as JSON
    if row:
        state, time = row
        print(f"Found data for device ID {robot_id}: Status={state}, Timestamp={time}")
        return jsonify({'status': state, 'timestamp': time})
    else:
        return jsonify({'status': 'No data yet', 'timestamp': None})


# Route for fetching robot data with specific time range and counting states
@app.route('/get_robot_data', methods=['GET'])
def get_robot_data():
    robot_id = request.args.get('robotId')
    start_time_str = request.args.get('dateTimeFrom')
    end_time_str = request.args.get('dateTimeTo')

    print(f"Received request for device ID {robot_id} from {start_time_str} to {end_time_str}")

    # Convert start and end time strings to datetime objects
    start_time = datetime.fromisoformat(start_time_str)
    end_time = datetime.fromisoformat(end_time_str)

    # Connect to the SQLite database
    conn = sqlite3.connect("robot_data.db")
    cursor = conn.cursor()

    # Query to get the count and total duration in seconds for each robot state
    cursor.execute(
        """
         SELECT
        r1.state,
        COUNT(DISTINCT r1."time") AS count,
        SUM(
            CASE
                WHEN r1.state = 'DOWN' THEN
                    (strftime('%s', r2."time") - strftime('%s', r1."time")) / 10
                ELSE
                    strftime('%s', r2."time") - strftime('%s', r1."time")
            END
        ) AS total_duration_seconds
    FROM
        robot_data r1
    LEFT JOIN
        robot_data r2 ON r1.device_id = r2.device_id AND r2."time" > r1."time"
    LEFT JOIN
        robot_data r3 ON r1.device_id = r3.device_id AND r3."time" > r1."time" AND r3."time" < r2."time"
    WHERE
        r1.device_id = ? AND r1."time" BETWEEN ? AND ?
        AND r3."time" IS NULL -- Exclude rows where there's a transition within the selected time range
    GROUP BY
        r1.state;
        """,
        (robot_id, start_time, end_time)
    )

    # Fetch the results
    state_counts = defaultdict(lambda: {'count': 0, 'total_duration_seconds': 0})
    for state, count, total_duration_seconds in cursor.fetchall():
        state_counts[state]['count'] = count
        state_counts[state]['total_duration_seconds'] = total_duration_seconds
        print(f"Found {count} rows with state {state}, total duration: {total_duration_seconds} milli? seconds")

    # Close the connection
    conn.close()

    # Convert total duration from seconds to hours and minutes
    for state_data in state_counts.values():
        total_duration_seconds = state_data['total_duration_seconds']

        # Calculate hours and minutes
        hours = total_duration_seconds // 3600 //60
        minutes = (total_duration_seconds % 3600) // 60

        # Update the state_data dictionary with hours and minutes
        state_data['total_duration_hours'] = hours
        state_data['total_duration_minutes'] = minutes

        # state_data['total_duration_hours'] = total_duration_seconds // 3600
        # state_data['total_duration_minutes'] = (total_duration_seconds % 3600) // 60

    # Return data as JSON
    return jsonify(state_counts)

# Route for fetching robot data with specific time range and counting states
@app.route('/get_robot_data_count', methods=['GET'])
def get_robot_data_count():
    robot_id = request.args.get('robotId')
    start_time_str = request.args.get('startTime')
    end_time_str = request.args.get('endTime')

    print(f"Received request for device ID {robot_id} from {start_time_str} to {end_time_str}")

    # Convert string representations of time to datetime objects
    start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
    end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')

    # Connect to the SQLite database
    conn = sqlite3.connect("robot_data.db")
    cursor = conn.cursor()

    # Query to get the count of occurrences for each robot state
    cursor.execute(
        "SELECT state, COUNT(*) FROM robot_data "
        "WHERE device_id = ? AND time BETWEEN ? AND ? "
        "GROUP BY state",
        (robot_id, start_time, end_time)
    )

    # Fetch the results
    state_counts = defaultdict(int)
    for state, count in cursor.fetchall():
        state_counts[state] = count

    # Close the connection
    conn.close()

    # Return data as JSON
    return jsonify(state_counts)

# Add a new route to fetch all rows from the database
@app.route('/get_all_rows', methods=['GET'])
def get_all_robot_data():
    # Connect to the SQLite database
    conn = sqlite3.connect("robot_data.db")
    cursor = conn.cursor()

    # Fetch all data from the table
    cursor.execute(
        "SELECT ID, device_id, state, strftime('%Y-%m-%d %H:%M:%S', time) "
        "FROM robot_data ORDER BY time DESC"
    )
    all_rows = cursor.fetchall()

    # Close the connection
    conn.close()

    # Return data as JSON
    return jsonify(all_rows)


# Route for fetching robot data with specific time range and counting states
@app.route('/get_robot_data_piechart', methods=['GET'])
def get_robot_data_piechart():
    robot_id = request.args.get('robotId')
    start_time_str = request.args.get('dateTimeFrom')
    end_time_str = request.args.get('dateTimeTo')

    print(f"Received request for device ID {robot_id} from {start_time_str} to {end_time_str}")

    # Convert start and end time strings to datetime objects
    start_time = datetime.fromisoformat(start_time_str)
    end_time = datetime.fromisoformat(end_time_str)

    # Connect to the SQLite database
    conn = sqlite3.connect("robot_data.db")
    cursor = conn.cursor()

    # Query to get the count and total duration in seconds for each robot state
    cursor.execute(
        """
        SELECT
            r1.state,
            COUNT(DISTINCT r1."time") AS count,
            SUM(
                CASE
                    WHEN r1.state = 'DOWN' THEN
                        (strftime('%s', r2."time") - strftime('%s', r1."time")) / 10
                    ELSE
                        strftime('%s', r2."time") - strftime('%s', r1."time")
                END
            ) AS total_duration_seconds
        FROM
            robot_data r1
        LEFT JOIN
            robot_data r2 ON r1.device_id = r2.device_id AND r2."time" > r1."time"
        LEFT JOIN
            robot_data r3 ON r1.device_id = r3.device_id AND r3."time" > r1."time" AND r3."time" < r2."time"
        WHERE
            r1.device_id = ? AND r1."time" BETWEEN ? AND ?
            AND r3."time" IS NULL -- Exclude rows where there's a transition within the selected time range
        GROUP BY
            r1.state;
        """,
        (robot_id, start_time, end_time)
    )

    # Fetch the results
    state_counts = defaultdict(lambda: {'count': 0, 'total_duration_seconds': 0})
    for state, count, total_duration_seconds in cursor.fetchall():
        state_counts[state]['count'] = count
        state_counts[state]['total_duration_seconds'] = total_duration_seconds
        print(f"Found {count} rows with state {state}, total duration: {total_duration_seconds} seconds")

    # Close the connection
    conn.close()

    # Prepare data for the pie chart
    labels = list(state_counts.keys())
    data = [state_counts[state]['count'] for state in labels]

    return render_template('pie_chart.html', labels=labels, data=data)



if __name__ == '__main__':
    app.run(debug=True)
