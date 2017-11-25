#ifndef PACKET_H
#define PACKET_H

#include <stdint.h>

typedef struct alma_packet {
    uint8_t     start_code[2];
    uint16_t    length;
    uint8_t     id;
    void        *data;
    uint8_t     crc;
} alma_packet;

uint8_t packet_calc_crc(const alma_packet *packet);

#endif
