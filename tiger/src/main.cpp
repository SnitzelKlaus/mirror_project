#include <Arduino.h>

void setup() {
  Serial.begin(19200);
  pinMode(A0, OUTPUT);
  pinMode(A1, OUTPUT);
  pinMode(A2, OUTPUT);
  pinMode(A3, OUTPUT);

}

void loop() {

  int sensor0Value = analogRead(A0);
  float voltage0= sensor0Value * (5.0 / 1023.0);

  int sensor1Value = analogRead(A1);
  float voltage1= sensor1Value * (5.0 / 1023.0);
  
  int sensor2Value = analogRead(A2);
  float voltage2= sensor2Value * (5.0 / 1023.0);
  
  int sensor3Value = analogRead(A3);
  float voltage3= sensor3Value * (5.0 / 1023.0);


  Serial.println((String) "0:" + voltage0);
  Serial.println((String) "1:" + voltage1);
  Serial.println((String) "2:" + voltage2);
  Serial.println((String) "3:" + voltage3);

  delay(100);
}