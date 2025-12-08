#include <Wire.h>
#include "Adafruit_MCP9600.h"
#include "config.h"

Adafruit_MCP9600 sensors[SENSOR_COUNT];

// Select TCA channel (Multiplexer)
void tcaselect(uint8_t channel) {
  if (channel > 7) return;
  Wire.beginTransmission(TCA_ADDRESS);
  Wire.write(1 << channel);
  Wire.endTransmission();
}

void setup() {
  Serial.begin(BAUDRATE);
  while (!Serial);

  Serial.println("Initializing MCP9600 sensors.....");
  Wire.begin();

  // Initialize all sensors
  for (uint8_t i = 0; i < SENSOR_COUNT; i++) {
    Serial.print("Selecting TCA channel");
    Serial.println(SENSOR_CHANNEL[i]);

    tcaselect(SENSOR_CHANNEL[i]);
    delay(CHANNEL_SWITCH_DELAY_MS);

    if (!sensors[i].begin(MCP9600_ADDRESS)) {
      Serial.print("ERROR: MCP9600 NOT FOUND at sensor index");
      Serial.println(i);
      continue;
    }
    
    sensors[i].setThermocoupleType(SENSOR_TC_TYPE[i]);
    sensors[i].setADCresolution(SENSOR_ADC[i]);
    sensors[i].enable(true);

    Serial.print("Sensor");
    Serial.print(i);
    Serial.println("initialized");
  }

  Serial.println("READY");
}



void loop() {
  for (uint8_t i = 0; i < SENSOR_COUNT; i++) {

    tcaselect(SENSOR_CHANNEL[i]);
    delay(CHANNEL_SWITCH_DELAY_MS);

    float hot  = sensors[i].readThermocouple(); // main temperature
    float cold = sensors[i].readAmbient();      // reference cold junction

    // Print HOT value
    Serial.print(hot);
    Serial.print(",");

    // Print COLD value
    Serial.print(cold);

    if (i < SENSOR_COUNT - 1) {
      Serial.print(",");
    }
  }

  Serial.println();
  delay(READ_INTERVAL_MS);
}
