#ifndef CRC8_H
#define CRC8_H

#include <stdint.h>

extern const uint8_t crc8_polynomial;
extern const uint8_t crc8_table[];

uint8_t crc8_calculate(const uint8_t *data, uint16_t length);

#endif
