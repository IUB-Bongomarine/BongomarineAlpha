#include "compassAndGyro.h"  // handles analog write
#include "pingAndBar.h"      // handles analog write
#include "thruster.h"        // handles thrusters
// Servo object for thrusters

void setup() {
  Serial.begin(115200);  //uncomment only if the setupOTA is commented
  Wire.begin();
//  setupPing();
  pinMode(6, INPUT);
  
  setupBar();
  setupCompassAndGyro();
  setupThruster();
}

void loop() {
  
//  updatePing();            // pingDistance and pingConfidence
  updateBar();             // barPressure, barTemperature, barDepth, and barAltitude
  updateCompassHeading();  // headingDegrees is being updated with kalman filter.
  updateGyroReading();  
   if (!digitalRead(6)) {
    pingFlag = false;
    headingControlEnabled = false;
    stopAllMotors();
    horizontalRightThrust = 1500;
    horizontalLeftThrust = 1500;
    verticalRightThrust = 1500;
    verticalLeftThrust = 1500;
    step = 0;
  } else {
    runScripted();
  }
  
  // agz is being updated with kalman filter.
  error = hoverHeight - barDepth;
  if (pingFlag) {
    controlHover(barDepth);
  }
  if (headingControlEnabled) {
    updateHeadingControl();
  }
  // runThruster();
     String debugMessage = String(headingDegrees) + "\t" + String(barPressure);
//  String print = String(agz) + "," + String(headingDegrees) + "," + String(pingDistance) + "," + String(pingConfidence) + "," + String(barPressure) + "," + String(barDepth) + "," + String(barTemperature) + "," + String(barAltitude) + "," + String(horizontalRightThrust) + "," + String(horizontalLeftThrust) + "," + String(verticalRightThrust) + "," + String(verticalLeftThrust);
  Serial.println(debugMessage);
//  Serial.print(",");
//  Serial.println(error);
  // runAuto();
}
