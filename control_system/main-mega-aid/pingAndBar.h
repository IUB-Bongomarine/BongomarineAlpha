#include "ping1d.h"
// #include <Wire.h>
#include "MS5837.h"

static const uint8_t arduinoRxPin = 19; // Serial1 rx
static const uint8_t arduinoTxPin = 18; // Serial1 tx

static Ping1D ping { Serial1 };
float pingDistance = 0;
float pingConfidence = 0;

float barPressure = 0;
float barTemperature = 0;
float barDepth = 0;
float barAltitude = 0;

MS5837 sensor;

void setupPing() {
  Serial1.begin(115200);
  while (!ping.initialize()) {
    Serial.println("Ping Error");
    delay(2000);
  }
}

void updatePing() {
  if (ping.update()) {
    pingDistance = ping.distance(); // in cm
    pingConfidence = ping.confidence();
  }
}

void setupBar() {
  Wire.begin();

  // Initialize pressure sensor
  // Returns true if initialization was successful
  // We can't continue with the rest of the program unless we can initialize the sensor
  while (!sensor.init()) {
    Serial.println("Bar Error");
  }
  
  sensor.setModel(MS5837::MS5837_30BA);
  sensor.setFluidDensity(997); // kg/m^3 (freshwater, 1029 for seawater)
}

void updateBar() {
  // Update pressure and temperature readings
  sensor.read();
  barPressure = sensor.pressure(); 
  barTemperature = sensor.temperature(); 
  barDepth = sensor.depth() * 100; 
  barAltitude = sensor.altitude();
}
