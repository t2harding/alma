#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import(print_function)

__version__ = filter(str.isdigit, '$Revision: $')

import logging
import sys

class CRC8(object):
    """
    CRC8 algorithm
    """
    def __init__(self, polynomial=0x07):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('__init__')

        self.polynomial = polynomial
        self.logger.debug('polynomial = 0x{:02x}'.format(self.polynomial))

        return

    def generate_table(self, output_file = sys.stdout, language = 'c'):
        self.logger.debug('generate_table({},{})'.format(repr(output_file),repr(language)))
        if language == 'c':
            print('const uint8_t crc8_polynomial = 0x{:02x}'.format(self.polynomial))
            print('const uint8_t crc8_table[] = {', file=output_file)
        elif language == 'python':
            print('CRC8_POLYNOMIAL = 0x{:02x}'.format(self.polynomial))
            print('CRC8_TABLE = {', file=output_file)

        for divident in range(0,256):
            current_byte = divident
            if divident % 8 == 0:
                if language == 'c':
                    output_file.write('                              ')
                elif language == 'python':
                    output_file.write('              ')
            for bit in range(0,8):
                if (current_byte & 0x80) != 0:
                    current_byte = current_byte << 1
                    current_byte = current_byte ^ self.polynomial
                else:
                    current_byte = current_byte << 1
                current_byte = current_byte & 0xff
            output_file.write('0x{:02x},'.format(current_byte))
            if divident % 8 == 7:
                output_file.write('\n')

        if language == 'c':
            print('                             };', file=output_file)
        elif language == 'python':
            print('             }', file=output_file)

    def calculate(self, data):
        self.logger.debug('calculate({})'.format(repr(data)))


if __name__ == '__main__':
    import argparse
    import random
    import time
    import packet

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='Generate CRC8 Table')

    parser.add_argument('-f', '--file',
                        help='File to write the output to',
                        default=sys.stdout)
    parser.add_argument('-p', '--polynomial',
                        help='Polynomial to use in generating CRC8 table',
                        type=int,
                        default=0x07)
    parser.add_argument('-v', '--verbose',
                        help='Set verbosity level',
                        action='count')

    args = parser.parse_args()

    # Setup the logger
    logging.basicConfig(format='%(asctime)s: [%(levelname)-7s] %(name)-10s| %(message)s')
    root_logger = logging.getLogger()

    if args.verbose > 1:
        root_logger.setLevel(logging.DEBUG)
    elif args.verbose > 0:
        root_logger.setLevel(logging.INFO)

    crc8 = CRC8(args.polynomial)
    crc8.generate_table(args.file)
