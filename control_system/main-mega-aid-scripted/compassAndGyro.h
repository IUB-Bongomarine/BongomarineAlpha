#include "Wire.h"
#include "I2Cdev.h"
#include "MPU6050.h"
#include "QMC5883LCompass.h"

MPU6050 accelgyro;
QMC5883LCompass compass;

unsigned long now, lastTime = 0;
float dt;  //time

int16_t ax, ay, az, gx, gy, gz;                              //Accelerometer Gyro Raw Data
float aax = 0, aay = 0, aaz = 0, agx = 0, agy = 0, agz = 0;  //Angle variable
long axo = 0, ayo = 0, azo = 0;                              //Accelerometer offset
long gxo = 0, gyo = 0, gzo = 0;                              //Gyroscope offset

float pi = 3.1415926;
float AcceRatio = 16384.0;                                //Accelerometer scaling factor
float GyroRatio = 131.0;                                  //Gyro scale factor
uint8_t n_sample = 8;                                     //Accelerometer Filter Algorithm Samples
float aaxs[8] = { 0 }, aays[8] = { 0 }, aazs[8] = { 0 };  //x,yAxis sampling queue
long aax_sum, aay_sum, aaz_sum;                           //x,yAxis sampling and

float a_x[10] = { 0 }, a_y[10] = { 0 }, a_z[10] = { 0 }, g_x[10] = { 0 }, g_y[10] = { 0 }, g_z[10] = { 0 };
float Px = 1, Rx, Kx, Sx, Vx, Qx;  //x Axis Kalman Variable
float Py = 1, Ry, Ky, Sy, Vy, Qy;  //y Axis Kalman Variable
float Pz = 1, Rz, Kz, Sz, Vz, Qz;

float headingDegrees = 0;  // compass reading in degrees

void setupCompassAndGyro() {
  // Serial.begin(115200);
  compass.init();
  accelgyro.initialize();
  Serial.println("Compass Kando");
  unsigned short times = 200;  //Number of samples
  for (int i = 0; i < times; i++) {
    accelgyro.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);  //Read six-axis raw values
    axo += ax;
    ayo += ay;
    azo += az;  //Sampling and
    gxo += gx;
    gyo += gy;
    gzo += gz;
  }
  axo /= times;
  ayo /= times;
  azo /= times;  //Calculate accelerometer offset
  gxo /= times;
  gyo /= times;
  gzo /= times;  //Calculating Gyro Offset
}

void updateCompassHeading() {
  compass.read();

  float heading = atan2(compass.getY(), compass.getX());

  // Update this value with the current declination for Dhaka
  float declinationAngle = -0.53;          // Magnetic declination in degrees
  heading += declinationAngle * PI / 180;  // Convert declination to radians

  if (heading < 0)
    heading += 2 * PI;
  if (heading > 2 * PI)
    heading -= 2 * PI;

  headingDegrees = heading * 180 / M_PI;
}

// updates compass and gyro readings with kalman filter. agz and headingDegrees are the global variables that are being updated
void updateGyroReading() {

  unsigned long now = millis();    //current time(ms)
  dt = (now - lastTime) / 1000.0;  //Differential time(s)
  lastTime = now;                  //Last sampling time(ms)

  accelgyro.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);  //Read six-axis raw values

  float accx = ax / AcceRatio;  //x Axis acceleration
  float accy = ay / AcceRatio;  //y Axis acceleration
  float accz = az / AcceRatio;  //z Axis acceleration

  aax = atan(accy / accz) * (-180) / pi;  //y Angle of the axis to the z axis
  aay = atan(accx / accz) * 180 / pi;     //x Angle of the axis to the z axis
                                          //z Angle of the axis to the z axis

  aax_sum = 0;  // Sliding weighted filtering algorithm for accelerometer raw data
  aay_sum = 0;


  for (int i = 1; i < n_sample; i++) {
    aaxs[i - 1] = aaxs[i];
    aax_sum += aaxs[i] * i;
    aays[i - 1] = aays[i];
    aay_sum += aays[i] * i;
    aazs[i - 1] = aazs[i];
    aaz_sum += aazs[i] * i;
  }

  aaxs[n_sample - 1] = aax;
  aax_sum += aax * n_sample;
  aax = (aax_sum / (11 * n_sample / 2.0)) * 9 / 7.0;
  aays[n_sample - 1] = aay;
  aay_sum += aay * n_sample;
  aay = (aay_sum / (11 * n_sample / 2.0)) * 9 / 7.0;
  aazs[n_sample - 1] = aaz;
  aaz_sum += aaz * n_sample;
  aaz = (aaz_sum / (11 * n_sample / 2.0)) * 9 / 7.0;

  float gyrox = -(gx - gxo) / GyroRatio * dt;
  float gyroy = -(gy - gyo) / GyroRatio * dt;
  agx += gyrox;
  agy += gyroy;

  /* kalman start */
  Sx = 0;
  Rx = 0;
  Sy = 0;
  Ry = 0;

  for (int i = 1; i < 10; i++) {
    a_x[i - 1] = a_x[i];
    Sx += a_x[i];
    a_y[i - 1] = a_y[i];
    Sy += a_y[i];
    a_z[i - 1] = a_z[i];
    Sz += a_z[i];
  }

  a_x[9] = aax;
  Sx += aax;
  Sx /= 10;
  a_y[9] = aay;
  Sy += aay;
  Sy /= 10;
  a_z[9] = aaz;
  Sz += aaz;
  Sz /= 10;

  for (int i = 0; i < 10; i++) {
    Rx += sq(a_x[i] - Sx);
    Ry += sq(a_y[i] - Sy);
    Rz += sq(a_z[i] - Sz);
  }

  Rx = Rx / 9;
  Ry = Ry / 9;
  Rz = Rz / 9;

  Px = Px + 0.0025;
  Kx = Px / (Px + Rx);
  agx = agx + Kx * (aax - agx);
  Px = (1 - Kx) * Px;

  Py = Py + 0.0025;
  Ky = Py / (Py + Ry);
  agy = agy + Ky * (aay - agy);
  Py = (1 - Ky) * Py;

  Pz = Pz + 0.0025;
  Kz = Pz / (Pz + Rz);
  Pz = (1 - Kz) * Pz;

  float gyroZChange = -(gz - gzo) / GyroRatio;  // Calculate Z-axis rotation rate
  if (abs(gyroZChange) * dt > 0.1) {            // Check for significant gyro change
    agz += gyroZChange * dt;                    // Update yaw only if there's significant gyro change
  }
}
