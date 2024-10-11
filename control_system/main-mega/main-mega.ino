#include "compassAndGyro.h"  // handles analog write
#include "pingAndBar.h"      // handles analog write
#include "thruster.h"        // handles thrusters
// Servo object for thrusters

void setup() {
  Serial.begin(115200);  //uncomment only if the setupOTA is commented
  Wire.begin();
  setupPing();
  setupThruster();
  setupBar();
  setupCompassAndGyro();
}

void loop() {
  updatePing();            // pingDistance and pingConfidence
  updateBar();             // barPressure, barTemperature, barDepth, and barAltitude
  updateCompassHeading();  // headingDegrees is being updated with kalman filter.
  updateGyroReading();     // agz is being updated with kalman filter.
//  if (barDistance < maxHeight) {
//    maxHeight = barDistance;
//  }
  if (pidFlag) {
    doPid();
  }
  //  if (pingFlag && pingConfidence > 96) {
//  float error = hoverHeight - barDepth;
//  Serial.print("Error:");
//  Serial.println(error);
  if (pingFlag) {
    controlHover(barDepth);
  }
  runThruster();
  //   String print = String(headingDegrees) + "\t";
  String print = String(agz) + "," + String(headingDegrees) + "," + String(pingDistance) + "," + String(pingConfidence) + "," + String(barPressure) + "," + String(barDepth) + "," + String(barTemperature) + "," + String(barAltitude) + "," + String(horizontalRightThrust) + "," + String(horizontalLeftThrust) + "," + String(verticalRightThrust) + "," + String(verticalLeftThrust);
  Serial.println(print);
}
