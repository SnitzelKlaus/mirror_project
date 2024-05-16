#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ArduinoJson.h>

// Wi-Fi credentials
const char *ssid = "CEASAR";
const char *password = "V3ryN1ce!";

// Web server on port 6942
ESP8266WebServer server(6942);

// TCP debugging server on port 4269
WiFiServer debugServer(4269);
WiFiClient debugClient;

void setup() {
  // Serial communication for ATmega328P
  Serial.begin(19200);

  WiFi.begin(ssid, password);
  
  // Attempt to connect to Wi-Fi
  int retries = 20;
  while (WiFi.status() != WL_CONNECTED && retries > 0) {
    delay(1000);
    retries--;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("DEBUG: Connected to Wi-Fi");
    Serial.println("DEBUG: IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("DEBUG: Failed to connect to Wi-Fi");
    Serial.println("DEBUG: Wi-Fi Status Code: ");
    Serial.println(WiFi.status());
    return;
  }

  debugServer.begin(); // Start debugging server

  server.on("/update", HTTP_POST, []() {
    if (server.hasArg("plain") == false) {
      server.send(204, "text/plain", "Body not received");
      if (debugClient) {
        debugClient.println("DEBUG: Body not received");
      }
      return;
    }

    String body = server.arg("plain");
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, body);
    
    if (error) {
      server.send(500, "text/plain", "Error parsing JSON");
      if (debugClient) {
        debugClient.println("DEBUG: Error parsing JSON");
      }
      return;
    }

    // Extract positions from JSON
    int baseDeg = doc["base"];
    int shoulderDeg = doc["shoulder"];
    int elbowDeg = doc["elbow"];
    int wristDeg = doc["wrist"];
    int wristRotDeg = doc["wristRot"];
    int gripperDeg = doc["gripper"];

    // Data validation
    if (baseDeg < 0 || baseDeg > 180 || shoulderDeg < 15 || shoulderDeg > 165 || 
        elbowDeg < 0 || elbowDeg > 180 || wristDeg < 0 || wristDeg > 180 || 
        wristRotDeg < 0 || wristRotDeg > 180 || gripperDeg < 10 || gripperDeg > 73) {
      server.send(400, "text/plain", "Invalid data");
      if (debugClient) {
        debugClient.println("DEBUG: Invalid data");
      }
      return;
    }
    
    // Command to send to ATmega328P
    String command = String(baseDeg) + "," + String(shoulderDeg) + "," + 
                     String(elbowDeg) + "," + String(wristRotDeg) + "," + 
                     String(wristDeg) + "," + String(gripperDeg);
    
    Serial.println(command);

    server.send(200, "text/plain", "Positions updated");
  });

  server.begin();
}

void loop() {
  server.handleClient();

  if (debugServer.hasClient()) {
    debugClient = debugServer.accept();
  }

  // Read debug data from ATmega328P
  while (Serial.available()) {
    char c = Serial.read();
    if (debugClient) {
      debugClient.write(c);
    }
  }
}
