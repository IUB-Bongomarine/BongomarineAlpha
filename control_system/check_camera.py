import cv2
import subprocess
import platform

def list_cameras_linux():
    print("Listing cameras on Linux/Raspberry Pi...")
    devices = subprocess.check_output('ls /dev/video*', shell=True).decode('utf-8').strip().split('\n')
    for device in devices:
        print(f"Found device: {device}")

def list_cameras_mac():
    print("Listing cameras on macOS...")
    result = subprocess.run(['system_profiler', 'SPCameraDataType'], stdout=subprocess.PIPE)
    cameras = [line for line in result.stdout.decode('utf-8').split('\n') if 'Model ID' in line or 'Unique ID' in line]
    for camera in cameras:
        print(f"Found device: {camera}")

def list_cameras_windows():
    print("Listing cameras on Windows...")
    import win32com.client
    objWMI = win32com.client.GetObject('winmgmts:').InstancesOf('Win32_PnPEntity')
    for obj in objWMI:
        if obj.Name and ('camera' in obj.Name.lower() or 'webcam' in obj.Name.lower()):
            print(f"Found device: {obj.Name}")

def check_cameras():
    print("Checking available cameras with OpenCV...")
    camera_id = 0
    while True:
        try:
            cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)  # Using CAP_DSHOW for Windows compatibility
            if cap.isOpened():
                print(f"OpenCV can access camera ID {camera_id}")
                cap.release()
            else:
                print(f"No more cameras to check, stopped at ID {camera_id}")
                break
        except Exception as e:
            print(f"Error accessing camera ID {camera_id}: {e}")
            break
        camera_id += 1

if __name__ == "__main__":
    os_type = platform.system()
    if os_type == "Linux":
        list_cameras_linux()
    elif os_type == "Darwin":  # macOS is identified as 'Darwin'
        list_cameras_mac()
    elif os_type == "Windows":
        list_cameras_windows()
    else:
        print(f"Unsupported operating system: {os_type}")

    check_cameras()