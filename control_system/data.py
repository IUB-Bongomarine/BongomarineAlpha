import os
import sys
import serial
import threading
import csv
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Set the Arduino serial port based on the operating system
if sys.platform.startswith('win'):
    arduino_port = 'COM18'  # Replace 'COM3' with the appropriate port on Windows
elif sys.platform.startswith('linux'):
    arduino_port = '/dev/ttyUSB0'  # Replace '/dev/ttyUSB0' with the appropriate port on Linux
elif sys.platform.startswith('darwin'):
    arduino_port = '/dev/cu.usbmodem14201'  # Replace '/dev/cu.usbmodem14201' with the appropriate port on macOS
else:
    print("Unsupported operating system")
    sys.exit(1)

ser = serial.Serial(arduino_port, 9600, timeout=0.1)

def read_serial_data():
    # Create a unique filename with a timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f'test_data_{timestamp}.csv'
    
    # Define your column headers, change these as per your serial data
    headers = ['Timestamp', 'Sensor1', 'Sensor2', 'Sensor3']  # Add more headers as needed

    # Check if the file exists and has content (headers)
    file_exists = os.path.isfile(filename) and os.path.getsize(filename) > 0

    # Open or create a CSV file to store the data
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        # Write the header only if the file is newly created or empty
        if not file_exists:
            writer.writerow(headers)
            
        while True:
            if ser.inWaiting() > 0:
                data = ser.readline().decode().strip()
                if data:
                    # Split the data based on commas
                    data_list = data.split(',')
                    # Adds a timestamp
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    writer.writerow([current_time] + data_list)
                    file.flush()

try:
    ser.close()
    print(f"Connected to Arduino on {arduino_port}")
    if not ser.isOpen():
        ser.open()
        print('COM PORT is open', ser.isOpen())

    # Start the serial reading thread
    threading.Thread(target=read_serial_data, daemon=True).start()

    @app.route('/')
    def index():
        return render_template('gamepad.html')

    @app.route('/control', methods=['POST'])
    def control():
        direction = request.form['direction']
        ser.write(direction.encode())
        return jsonify({'status':'OK'})

    if __name__ == '__main__':
        app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)

except serial.SerialException as e:
    print(f"Failed to connect to Arduino on {arduino_port}: {e}")
    ser.close()
    sys.exit(1)
