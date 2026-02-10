#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>
#include "Adafruit_MCP9600.h"

#define BAUDRATE 115200

/*
   Number of MCP9600 sensors installed.
*/
const uint8_t SENSOR_COUNT = 8;

/*
   TCA9548A channel mapping for each sensor.
*/
const uint8_t SENSOR_CHANNEL[SENSOR_COUNT] = {
  4,  // Sensor 0 on channel 0
  5,  // Sensor 1 on channel 1
  6,  // Sensor 2 on channel 2
  7,  // Sensor 3 on channel 3
  0,  // Sensor 4 on channel 4
  1,  // Sensor 5 on channel 5
  2,  // Sensor 6 on channel 6
  3   // Sensor 7 on channel 7
};

/*
   Thermocouple type per sensor.
*/
const MCP9600_ThemocoupleType SENSOR_TC_TYPE[SENSOR_COUNT] = {
  MCP9600_TYPE_K,  // Sensor 0 type
  MCP9600_TYPE_K,  // Sensor 1 type
  MCP9600_TYPE_K,  // Sensor 2 type
  MCP9600_TYPE_K,  // Sensor 3 type
  MCP9600_TYPE_T,  // Sensor 4 type
  MCP9600_TYPE_T,  // Sensor 5 type
  MCP9600_TYPE_T,  // Sensor 6 type
  MCP9600_TYPE_T   // Sensor 7 type
};

/*
   ADC resolution for each sensor.
*/
const MCP9600_ADCResolution SENSOR_ADC[SENSOR_COUNT] = {
  MCP9600_ADCRESOLUTION_12,
  MCP9600_ADCRESOLUTION_12,
  MCP9600_ADCRESOLUTION_12,
  MCP9600_ADCRESOLUTION_12,
  MCP9600_ADCRESOLUTION_12,
  MCP9600_ADCRESOLUTION_12,
  MCP9600_ADCRESOLUTION_12,
  MCP9600_ADCRESOLUTION_12
};

/*
   Delay after switching TCA channel (ms)
*/
const uint8_t CHANNEL_SWITCH_DELAY_MS = 5;

/*
   Delay between reading cycles (ms)
*/
const uint16_t READ_INTERVAL_MS = 1000;

/*
   TCA multiplexer I2C address
*/
const uint8_t TCA_ADDRESS = 0x70;

/*
   MCP9600 I2C address (default = 0x67)
*/
const uint8_t MCP9600_ADDRESS = 0x67;

#endif
