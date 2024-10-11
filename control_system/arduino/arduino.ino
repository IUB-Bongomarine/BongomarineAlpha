void setup() {
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    char receivedChar = Serial.read();
    if (receivedChar == 'u') {
      // Move forward
      Serial.println("Upore");
    } else if (receivedChar == 'd') {
      // Move backward
      Serial.println("Niche");
    } else if (receivedChar == 'l') {
      // Turn left
      Serial.println("Baame");
    } else if (receivedChar == 'r') {
      // Turn right
      Serial.println("Daane");
    }
  }
}
