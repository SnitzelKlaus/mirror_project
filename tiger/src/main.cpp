  #include <Braccio.h>
  #include <Servo.h>

  Servo base;
  Servo shoulder;
  Servo elbow;
  Servo wrist_rot;
  Servo wrist_ver;
  Servo gripper;


  void setup() {
    // Setup serial communication at baudrate 9600 for reading the light sensor
    Serial.begin(9600);

    Braccio.begin();

    Braccio.ServoMovement(20, 0, 90, 90, 90, 90, 10);
  }




  long map(long x, long in_min, long in_max, long out_min, long out_max) {
      return (long)( (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min );
  }

  long GetCalibrateLightValue(long lightValue){
    long minValue = 4;
    long maxValue = 1023;

    // Serial.println("lightValue");
    // Serial.println(lightValue);

    long lightSenorValue = map(lightValue, minValue, maxValue, 0, 10000);

    return lightSenorValue;
  }


  void PrintLightValues(long lightValueAnalogZero, long lightValueAnalogOne, long lightValueAnalogTwo, long lightValueAnalogThree){

    Serial.println("Mapped light sensor value: ");
    //Serial.print(lightValue);
    Serial.println("A0");
    Serial.println(lightValueAnalogZero);

    Serial.println("A1");  
    Serial.println(lightValueAnalogOne);

    Serial.println("A2");
    Serial.println(lightValueAnalogTwo);
    
    Serial.println("A3");
    Serial.println(lightValueAnalogThree);
  }

  bool ValidateLightValues(long lightValueAnalogZero, long lightValueAnalogOne, long lightValueAnalogTwo, long lightValueAnalogThree) {
    long maxValue = 10000;
    return (lightValueAnalogZero == maxValue &&
            lightValueAnalogOne == maxValue &&
            lightValueAnalogTwo == maxValue &&
            lightValueAnalogThree == maxValue);
  }

  int stepDelay = 20;
  int moveBase = 100;
  int moveShoulder = 90;
  int moveElbow = 90;
  void MovesBraccioTowardsTheHighestLightValue(long lightValueAnalogZero, long lightValueAnalogOne, long lightValueAnalogTwo, long lightValueAnalogThree){
    // Move the Braccio arm towards the highest light sensor value
    if (lightValueAnalogZero + 10 <= lightValueAnalogThree) {
      // Move towards A0
          Serial.println("Move toward A0");
          moveElbow = moveElbow + 1;
      // Braccio.ServoMovement(20, 30, 90, 180, 90, 90, 10); // Move base towards A0 direction
    } 
    else if (lightValueAnalogZero >= lightValueAnalogThree + 10){
      // Move towards A3
      Serial.println("Move toward A3");
      moveElbow = moveElbow - 1;
      // Braccio.ServoMovement(20, 30, 90, 0, 90, 90, 10); // Move shoulder towards A3 direction
    }
    if (lightValueAnalogOne + 10 <= lightValueAnalogTwo) {
      // Move towards A1
          Serial.println("Move toward A1");
          if (moveBase < 0){
            moveBase = 175;
          }
          else{
            moveBase = moveBase - 1;
          }
          Serial.println(moveBase);

      // Braccio.ServoMovement(20, 140, 90, 0, 90, 90, 10); // Move base towards A1 direction
    } else if (lightValueAnalogOne >= lightValueAnalogTwo + 10)  {
      // Move towards A2
          Serial.println("Move toward A2");
          if (moveBase >= 180){
            moveBase = 5;
          }
          else{
            moveBase = moveBase + 1;
          }
          Serial.println(moveBase);

          
    }
      // Braccio.ServoMovement(20, 140, 90, 180, 90, 90, 10); // Move shoulder towards A2 direction
    Braccio.ServoMovement(stepDelay, moveBase, moveShoulder, moveElbow, 90, 90, 10);

  }

  void MoveBracioMovement(){
    int stepDelay = 20;
    int base = 180;
    int shoulder = 90;
    int elbow = 90;

    Braccio.ServoMovement(stepDelay, base, shoulder, elbow, 90, 90, 10);
  }

  void loop() {
    long lightValueAnalogZero = GetCalibrateLightValue(analogRead(A0));
    long lightValueAnalogOne = GetCalibrateLightValue(analogRead(A1));
    long lightValueAnalogTwo = GetCalibrateLightValue(analogRead(A2));
    long lightValueAnalogThree = GetCalibrateLightValue(analogRead(A3));

    PrintLightValues(lightValueAnalogZero, lightValueAnalogOne, lightValueAnalogTwo, lightValueAnalogThree);
    
    MovesBraccioTowardsTheHighestLightValue(lightValueAnalogZero, lightValueAnalogOne, lightValueAnalogTwo, lightValueAnalogThree);

    delay(100);
  }
