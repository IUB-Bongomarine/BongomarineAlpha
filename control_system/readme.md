# Project Name

## Description
This project is a sample application that utilizes `pyserial`, `flask`, and `jsonify` libraries.

## Installation
To install the required dependencies, follow the steps below:

1. Make sure you have Python installed on your system. You can download it from the official Python website: [https://www.python.org/downloads/](https://www.python.org/downloads/)

2. Open a terminal or command prompt and navigate to the project directory.

3. Create a virtual environment by running the following command: (Optional)
    ```
    python -m venv venv
    ```

4. Activate the virtual environment: (Optional)
    - On Windows:
      ```
      venv\Scripts\activate
      ```
    - On macOS and Linux:
      ```
      source venv/bin/activate
      ```

5. Install the required dependencies using `pip`:
    ```
    pip install pyserial flask jsonify
    pip install pyuac pypiwin32 (If using windows)
    ```

## Usage
To run the application, follow the steps below:

1. Make sure you have activated the virtual environment (if not already activated). (It is optional, only do it if you've created a virtual environment)

2. Run the check_camera.py file to identify the Camera index for opencv.

3. Change the camera = cv2.VideoCapture(1) in the runme.py file (Change 1 to your camera index).

4. (MUST DO) Add the required data parameters in the header array to add headers of the csv file.

5. Run the main script:
    ```
    Run "python data.py" if you want to run only the sensor data collection  and controller app.
    
    Run "python runme.py" if you want to run the sensor and video data collection and controller app.

    ```
6. Access the application in your web browser at `http://localhost:5000`.

## License
This project is licensed under the [GNU License](LICENSE).
