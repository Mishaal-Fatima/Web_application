import paho.mqtt.client as mqtt
import sqlite3
import json

# MQTT broker details
broker_address = "broker.mqttdashboard.com"
port = 1883
topic_template = "ii23/telemetry/+"

# SQLite database details
db_file = "robot_data.db"

# Callback when a new message is received
def on_message(client, userdata, msg):
    try:
        # Decode the received MQTT message
        mqtt_message = json.loads(msg.payload.decode())

        # Connect to the SQLite database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Insert MQTT data into the table
        cursor.execute("INSERT INTO robot_data (device_id, state, time) VALUES (?, ?, ?)",
                       (mqtt_message.get("deviceId"), mqtt_message.get("state"), mqtt_message.get("time")))
        conn.commit()

        # Close the connection
        conn.close()

        print(f"Inserted MQTT data into the DB: {mqtt_message}")

    except Exception as e:
        print(f"Error processing MQTT message: {e}")

# Create an MQTT client
client = mqtt.Client()
client.on_message = on_message

# Connect to the MQTT broker
client.connect(broker_address, port, 60)
client.subscribe(topic_template)

# Loop to stay connected and process incoming MQTT messages
client.loop_forever()

