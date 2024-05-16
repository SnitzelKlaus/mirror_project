#include <Braccio.h>
#include <Servo.h>

// Servo objects
Servo base;       // 0 - 180 Degrees
Servo shoulder;   // 15 - 165 Degrees
Servo elbow;      // 0 - 180 Degrees
Servo wrist_ver;  // 0 - 180 Degrees
Servo wrist_rot;  // 0 - 180 Degrees
Servo gripper;    // 10 - 73 Degrees

const int stepDelay = 10; // Delay between steps
const int dataReadDelay = 50; // Delay for reading data

void setup() {
  Serial.begin(19200);
  Braccio.begin();
}

void loop() {
  // Checks if there's any data available to read from serial
  if (Serial.available()) {
    // Wait a moment to let all data arrive
    delay(dataReadDelay);

    // Clears the buffer before reading new data
    while (Serial.available()) {
      char buffer[256];  // Buffer to store the data
      int bytesRead = Serial.readBytesUntil('\n', buffer, sizeof(buffer) - 1);
      buffer[bytesRead] = '\0';  // Null-terminate the string

      // Debug: Print received raw data
      Serial.print("DEBUG: Received: ");
      Serial.println(buffer);

      int positions[6];
      char* ptr = buffer;
      bool validData = true;

      // Parsing data
      for (int i = 0; i < 6 && validData; i++) {
        char* endPtr;
        long val = strtol(ptr, &endPtr, 10);
        if (ptr == endPtr) {  // Checks if strtol hasn't performed any conversion
          validData = false;
          Serial.println("DEBUG: Error: Invalid data format");
          break;
        }
        positions[i] = int(val);
        if (i < 5) {
          if (*endPtr != ',') {
            validData = false;
            Serial.println("DEBUG: Error: Not enough data points");
            break;
          }
          ptr = endPtr + 1;  // Move past the comma
        }
      }

      if (validData) {
        // Data validation
        if (positions[0] >= 0 && positions[0] <= 180 && 
            positions[1] >= 15 && positions[1] <= 165 && 
            positions[2] >= 0 && positions[2] <= 180 && 
            positions[3] >= 0 && positions[3] <= 180 && 
            positions[4] >= 0 && positions[4] <= 180 && 
            positions[5] >= 10 && positions[5] <= 73) {
          Braccio.ServoMovement(stepDelay, positions[0], positions[1], positions[2], positions[3], positions[4], positions[5]);
          Serial.println("DEBUG: Moving robot arm...");
        } else {
          Serial.println("DEBUG: Error: Invalid data - Out of range");
        }
      } else {
        Serial.println("DEBUG: Error: Data parsing failed");
      }
    }
  }
}
