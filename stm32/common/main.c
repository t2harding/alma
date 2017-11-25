#include "packet.h"
#include <stdio.h>

// Test code for checking out the functionality of the common code.

int main(void)
{
    char my_data[] = "123456789";

    alma_packet my_packet;

    my_packet.data = my_data;
    my_packet.length = sizeof(my_data) - 1;

    printf("CRC8 = 0x%02x\n", packet_calc_crc(&my_packet));

    return 0;
}
