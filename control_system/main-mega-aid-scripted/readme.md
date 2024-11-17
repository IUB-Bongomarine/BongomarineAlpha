main function recieves sensor data from header files.

libraries used:
1. https://github.com/electroniccats/mpu6050
2. https://github.com/mprograms/QMC5883LCompass
3. https://github.com/bluerobotics/ping-arduino
4. https://github.com/bluerobotics/BlueRobotics_MS5837_Library
5. https://github.com/br3ttb/Arduino-PID-Library

header file description:
1. compassAndGyro: updates compass and gyro sensor data with kalman filter

to-do:
1. yaw control based on compass and gyro data
2. integrate ping and bar sensor file into the code
3. depth control based on ping and bar sensor

possible features:
1. check every i2c sensor, if they are initialized or not
2. make a debug panel with LEDS. each LED will be related to one sensor (i.e compass, MPU).
If any of the sensor fails in intialization, the related debug LED will light up.