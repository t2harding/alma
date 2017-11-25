#include "packet.h"
#include "crc8.h"

uint8_t packet_calc_crc(const alma_packet *packet)
{
    return crc8_calculate((uint8_t *)packet->data, packet->length);
}
