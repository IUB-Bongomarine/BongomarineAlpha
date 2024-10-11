from flask import Flask, render_template, request, jsonify, Response
from multiprocessing import Process, Value, Pipe
import threading
import cv2
import serial
import sys
import csv
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

def serial_process(arduino_port, parent_conn):
    try:
        ser = serial.Serial(arduino_port, 115200, timeout=1)
        print(f"Connected to serial port {arduino_port}")
    except Exception as e:
        print(f"Error establishing serial connection: {e}")
        return

    filename = f'test_data_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Timestamp', 'Data'])

        while True:
            if parent_conn.poll():  # Check if there's a message from the main process
                direction = parent_conn.recv()
                if direction in ['l', 'f', 'r', 'u', 'b', 'd', 's', 'p', 'o']:
                    ser.write(direction.encode())
            
            data = ser.readline().decode().strip()
            print(data)
            if data:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([timestamp, data])
                csvfile.flush()

def video_process(recording_flag, child_conn):
    #camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    #camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Set the width to 1280 pixels
    #camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Set the height to 720 pixels
    camera = cv2.VideoCapture(0)
    camera.set(3, 1280)
    camera.set(3, 720)
    #camera.set(cv2.CAP_PROP_FPS, 30)  # Set the frame rate to 30 fps

    fourcc = cv2.VideoWriter_fourcc('m','p','4','v')
    video_out = None

    def capture_frames():
        nonlocal video_out
        while True:
            ret, frame = camera.read()
            if not ret:
                continue

            if recording_flag.value and frame is not None:
                if video_out is None:
                    video_out = cv2.VideoWriter(f'test_video_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.mp4', fourcc, 12, (int(camera.get(3)), int(camera.get(4))))
                video_out.write(frame)

    threading.Thread(target=capture_frames, daemon=True).start()

    @app.route('/video_feed')
    def video_feed():
        def generate():
            while True:
                ret, frame = camera.read()
                if not ret:
                    continue
                ret, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/control', methods=['POST'])
    def control():
        nonlocal video_out, camera
        direction = request.form.get('direction')

        child_conn.send(direction)  # Send direction to the serial process

        if direction == 'start':
            recording_flag.value = 1
            return jsonify({'status': 'Recording started'})
        elif direction == 'stop':
            recording_flag.value = 0
            if video_out:
                video_out.release()
                video_out = None
                #camera.release()  # Releasing camera here for clean-up, consider managing resource more appropriately based on actual use case
            return jsonify({'status': 'Recording stopped'})

        return jsonify({'status': 'Command not recognized'})

    @app.route('/')
    def index():
        return render_template('gamepad.html')

    app.run(debug=False, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    # Determine the correct serial port
    arduino_port = '' 
    # Set the Arduino serial port based on the operating system
    if sys.platform.startswith('win'):
        arduino_port = 'COM18'  # Replace with the appropriate port on Windows
    elif sys.platform.startswith('linux'):
        arduino_port = '/dev/ttyUSB0'  # Replace with the appropriate port on Linux
    elif sys.platform.startswith('darwin'):
        arduino_port = '/dev/cu.usbmodem14201'  # Replace with the appropriate port on macOS

    # Set up shared memory and pipe for inter-process communication
    recording_flag = Value('i', 0)  # Shared memory integer
    parent_conn, child_conn = Pipe()  # Communication pipe between processes

    # Create and start the processes
    serial_proc = Process(target=serial_process, args=(arduino_port, parent_conn))
    video_proc = Process(target=video_process, args=(recording_flag, child_conn))

    serial_proc.start()
    video_proc.start()

    serial_proc.join()
    video_proc.join()
