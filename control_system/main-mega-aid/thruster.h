
int baseSpeed = 1500;    // Neutral position
const int forwardOffset = 0;  // Offset for forward movement.

//// SERVO STUFF ////
#include <Servo.h>

Servo horizontalServo1;  // right
Servo horizontalServo2;  // left
Servo verticalServo1;    // right
Servo verticalServo2;    // left

int horizontalRightThrust = 1500;
int horizontalLeftThrust = 1500;
int verticalRightThrust = 1500;
int verticalLeftThrust = 1500;

const int thrustIncrement = 10;  // Adjust the thrust increment/decrement as needed


// ping stuff
const int deadzone = 130; // in cm
bool pingFlag = false;
int hoverHeight = 0;
int maxHeight = 144;
int maxVerticalThrust = 250;
const int maxTopVerticalError = 40; // Maximum error before full speed
const int maxBottomVerticalError = 100; // Maximum error before full speed

void stopAllMotors() {
  verticalServo1.writeMicroseconds(1500);
  verticalServo2.writeMicroseconds(1500);
  horizontalServo1.writeMicroseconds(1500);
  horizontalServo2.writeMicroseconds(1500);
}

void setupThruster() {
  Serial.println("Setup started");
  // 3, 5, 7, 9
  horizontalServo1.attach(7); // right
  horizontalServo2.attach(9);
  verticalServo1.attach(5);  // vertical right
  verticalServo2.attach(3);

  stopAllMotors();

  Serial.println("Setup completed");
}

// horizontal motor stuff
float desiredHeading = 0;
bool headingControlEnabled = false;

void updateHeadingControl() {
  if (headingControlEnabled) {
    float currentHeading = headingDegrees;
    float headingError = desiredHeading - currentHeading;

    // Normalize the error to be within -180 to 180 degrees
    if (headingError > 180) headingError -= 360;
    else if (headingError < -180) headingError += 360;

    // Assuming error range of -180 to 180 maps to thrust differential of -500 to 500
    int thrustAdjustment = map(headingError, -180, 180, -250, 250);

    horizontalRightThrust = constrain(baseSpeed - thrustAdjustment, 1000, 2000);
    horizontalLeftThrust = constrain(baseSpeed + thrustAdjustment, 1000, 2000);
  }
}


// vertical motor stuff
float calculateMotorSpeed(float error) {
  float speed;
  // target er niche neme jaoar porer logic
  if (error < -5) {
    return 1500;
    speed = map(error, 0, maxBottomVerticalError, 1450, 1650);
  }
  // target er upore uthe jaoar porer logic
  if (error > -5) {
    // Up thrust
    speed = map(error, -5, maxTopVerticalError, 1650, 1700); // up thrust barate hobe
    return constrain(speed, 1650, 1700);
//        if (error > -15){
//          return constrain(0, 1350, 1700);
//        }
  }
  return constrain(speed, 1350, 1750);
}

float error = 0;

void controlHover(int currentDistance) {
  

  verticalLeftThrust = calculateMotorSpeed(error);
  verticalRightThrust = verticalLeftThrust;
}

void runThruster() {
  if (Serial.available() > 0) {
    char receivedChar = Serial.read();
    switch (receivedChar) {
      case 'f':
        // forward
        horizontalRightThrust += thrustIncrement;
        horizontalLeftThrust += thrustIncrement;
        if (headingControlEnabled) {
          baseSpeed += 10;
        }
        break;
      case 'b':
        // backward
        horizontalRightThrust -= thrustIncrement;
        horizontalLeftThrust -= thrustIncrement;
        if (headingControlEnabled) {
          baseSpeed -= 10;
        }
        break;
      case 'r':
        // right
        horizontalRightThrust -= thrustIncrement;
        horizontalLeftThrust += thrustIncrement;
        if (headingControlEnabled) {
          desiredHeading += 10;
        }
        break;
      case 'l':
        // left
        horizontalRightThrust += thrustIncrement;
        horizontalLeftThrust -= thrustIncrement;
        if (headingControlEnabled) {
          desiredHeading -= 10;
        }
        break;
      case 'u':
        // upward
        verticalRightThrust -= thrustIncrement;
        verticalLeftThrust -= thrustIncrement;
        break;
      case 'd':
        // downward
        verticalRightThrust += thrustIncrement;
        verticalLeftThrust += thrustIncrement;
        break;
      case 's':
        // stopAll
        horizontalRightThrust = 1500;
        horizontalLeftThrust = 1500;
        verticalRightThrust = 1500;
        verticalLeftThrust = 1500;
        baseSpeed = 1500;
        break;
      case 'p':
        headingControlEnabled = !headingControlEnabled;

        if (headingControlEnabled) {
          baseSpeed = horizontalRightThrust;
          updateCompassHeading();
          desiredHeading = headingDegrees;
        } else {
          horizontalRightThrust = 1500;
          horizontalLeftThrust = 1500;
        }
        updateHeadingControl();
        break;
      case 'o':
        pingFlag = !pingFlag;
        if (hoverHeight == 0) {
          hoverHeight = maxHeight / 2;
          Serial.print("Hovering Height: ");
          Serial.println(hoverHeight);
        }
        if (!pingFlag) {
          verticalRightThrust = 1500;
          verticalLeftThrust = 1500;
        }
        break;
    }
  }
  verticalServo1.writeMicroseconds(verticalRightThrust);
  verticalServo2.writeMicroseconds(verticalLeftThrust);
  horizontalServo1.writeMicroseconds(horizontalRightThrust);
  horizontalServo2.writeMicroseconds(horizontalLeftThrust);
}
