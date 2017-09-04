#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import(print_function)

__version__ = filter(str.isdigit, '$Revision: $')

import logging
import struct


PACKET_START_BYTES = (0xa1, 0x95)
PACKET_MAX_ID = 0xFF

class Packet(object):
    """
    Packet for serial data stream (Ethernet, RS232/RS422, etc)
    The basic format of the packet is:
      Start code = 0xa1 0x95
      Length = 2 bytes (Excludes start code and CRC)
      ID = 1 byte
      Data = (length - 1) * bytes
      CRC = 1 byte
    """
    def __init__(self, format='', id=0xFF, name='', element_names=None, element_values=None):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('__init__')

        self.format = format
        self.id = id
        self.name = name
        if element_names is not None:
            self.element_names = element_names

            index = 0
            for element_name in self.element_names:
                if element_values is not None:
                    setattr(self, element_name, element_values[index])
                else:
                    setattr(self, element_name, None)
                index += 1
        else:
            self.element_names = []

        self._log()

        return

    def _log(self):
        self.logger.debug('_log')
        self.logger.info('New packet')
        self.logger.info('  Name:   {}'.format(self.name))
        self.logger.info('  ID:     {}'.format(self.id))
        self.logger.info('  Length: {}'.format(struct.calcsize(self.format)))
        self.logger.info('  Format: {}'.format(self.format))
        self.logger.info('  Elements:')
        index = 0
        for element_name in self.element_names:
            self.logger.info('    {} = {}'.format(element_name, getattr(self, element_name)))
            index += 1

    def add_element(self, element_format, element_name, element_value):
        self.logger.debug('add_element({}, {}, {})'.format(repr(element_format), repr(element_name), repr(element_value)))
        if hasattr(self, element_name):
            raise ValueError
        else:
            self.logger.info('Adding {} = {}'.format(repr(element_name), element_value))
            self.format = self.format + element_format
            self.element_names.append(element_name)
            setattr(self, element_name, element_value)

    def pack(self):
        self.logger.debug('pack()')
        header = struct.pack('2BHB', PACKET_START_BYTES[0], PACKET_START_BYTES[1], struct.calcsize(self.format) + 6, self.id)
        return header + self._to_bytes() + struct.pack('B', 0xff)

    def unpack(self, data):
        self.logger.debug('unpack({})'.format(repr(data)))
        header = struct.unpack('2BHB', data[:5])
        self.logger.info('Unpacking {}'.format(repr(self.name)))
        self.logger.info('  Header:     {}'.format(repr(data[:5])))
        self.logger.info('  Start code: 0x{:02x}{:02x}'.format(header[0], header[1]))
        self.logger.info('  Size:       {}'.format(repr(header[2])))
        self.logger.info('  ID:         {}'.format(repr(header[3])))
        if header[0] != PACKET_START_BYTES[0] or header[1] != PACKET_START_BYTES[1]:
            self.logger.error('Bad start bytes 0xa195 != {}'.format(repr(header[0])))
            raise ValueError
        if header[3] != self.id:
            self.logger.error('Bad packet ID {} != {}'.format(repr(self.id), repr(header[1])))
            raise ValueError
        self._from_bytes(data[5:-1])

    def _to_bytes(self):
        self.logger.debug('_to_bytes()')
        data_list = []
        for element_name in self.element_names:
            data_list.append(getattr(self, element_name))

        return struct.pack(self.format, *data_list)

    def _from_bytes(self, bytes):
        self.logger.debug('_from_bytes({})'.format(repr(bytes)))
        data_list = struct.unpack(self.format, bytes)
        index = 0
        for element_name in self.element_names:
            setattr(self, element_name, data_list[index])
            index += 1

if __name__ == '__main__':
    import argparse
    import random
    import time

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='Test packet class')

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

    my_packet = Packet(format='iIcf12s',
                       id=0x01,
                       name='Test Packet',
                       element_names=['SIGNED_INT', 'UNSIGNED_INT', 'CHAR', 'FLOAT', 'STRING'],
                       element_values=[-2353, 1782, 'A', 28.1734, 'Sweet String'])

    receive_packet = Packet(format='iIcf12sd',
                            id=0x01,
                            name='Received Packet',
                            element_names=['SIGNED_INT', 'UNSIGNED_INT', 'CHAR', 'FLOAT', 'STRING', 'DOUBLE'])

    my_packet.add_element('d', 'DOUBLE', -13948.19834)
    try:
        my_packet.add_element('i', 'SIGNED_INT', -234) # This should cause an exception
    except ValueError:
        pass

    binary_data = my_packet.pack()

    print('{}'.format(repr(binary_data)))

    receive_packet.unpack(binary_data)

    receive_packet._log()

