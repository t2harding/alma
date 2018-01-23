#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import(print_function)

__version__ = filter(str.isdigit, '$Revision: $')

import socket
import logging
import threading
import select
import packet
import struct
import serial

class MyClient(object):
    """
    Client template
    """
    def __init__(self, dest=None, port=None, timeout=None, baudrate=9600, skt=None):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('__init__')

        self.logger.debug('  dest      = {}'.format(repr(dest)))
        self.logger.debug('  port      = {}'.format(repr(port)))
        self.logger.debug('  timeout   = {}'.format(repr(timeout)))
        self.logger.debug('  baudrate  = {}'.format(repr(baudrate)))
        self.logger.debug('  socket    = {}'.format(repr(skt)))

        self.clientsocket = None
        self.serialport = None
        self.timeout = timeout

        if skt is None:
            if dest is None:
                raise ValueError('Must specify an address/serial port or socket')
            # Check to see if we received an IP address or serial port
            try:
                sktaddr = socket.gethostbyname(dest)
                self.logger.info('Opening IP address {}'.format(repr(sktaddr)))
                self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.clientsocket.connect((sktaddr,port))
                self.logger.info('Client connected to {}'.format(self.clientsocket.getsockname()))
            except socket.gaierror:
                self.logger.info('Opening serial port {}'.format(repr(dest)))
                self.serialport = serial.Serial(dest, baudrate, timeout=self.timeout)
        else:
            self.clientsocket = skt

        if self.clientsocket is not None:
            # Non-blocking socket interface
            self.clientsocket.setblocking(0)

        self.logger.info('Creating data locks')
        self.packet_list_lock = threading.Lock()
        self.packet_list = [None] * packet.PACKET_MAX_ID

        return

    def add_packet(self, pkt):
        self.logger.debug('add_packet({})'.format(repr(pkt)))
        if self.packet_list[pkt.id] is not None:
            self.logger.warning('Packet ID 0x{:02x} already exists'.format(pkt.id))
        with self.packet_list_lock:
            self.packet_list[pkt.id] = pkt

    def set_timeout(self, timeout):
        self.logger.debug('set_timeout({})'.format(repr(timeout)))
        self.timeout = timeout
        if self.clientsocket is not None:
            self.clientsocket.settimeout(timeout)
        if self.serialport is not None:
            self.serialport.settimeout(timeout)

    def send_packet(self, pkt):
        self.logger.debug('send_packet({})'.format(repr(pkt)))
        bytes_sent = 0
        with self.packet_list_lock:
            packet_data = pkt.pack()
        while bytes_sent < len(packet_data):
            sent = self.clientsocket.send(packet_data[bytes_sent:])
            if sent == 0:
                self.logger.info('Sending socket has been closed')
                return False
            bytes_sent += sent
        return True

    def process_input(self, timeout=None):
        self.logger.debug('process_input({})'.format(repr(timeout)))
        if timeout is None:
            timeout = self.timeout
        ready_to_read, ready_to_write, in_error = select.select([self.clientsocket], [], [], timeout)
        for skt in ready_to_read:
            # Looking for the start code in the header
            start_byte_index = 0
            start_byte_found = False
            data_chunks = []
            self.logger.debug('Start code search:')
            while not start_byte_found:
                data_byte = skt.recv(1)
                if data_byte == '':
                    self.logger.info('Socket has been closed looking for Start code')
                    return False
                self.logger.debug('  index:  {}'.format(start_byte_index))
                self.logger.debug('  rx:     0x{:02x}'.format(ord(data_byte)))
                if ord(data_byte) == packet.PACKET_START_BYTES[start_byte_index]:
                    data_chunks.append(data_byte)
                    start_byte_index += 1
                else:
                    self.logger.info('  Start byte expected but not received')
                    data_chunks = []
                    start_byte_index = 0
                if start_byte_index > 1:
                    self.logger.debug('  Start code found')
                    start_byte_found = True
            packet_length = skt.recv(2)
            if packet_length == '':
                self.logger.info('Socket has been closed looking for packet length')
                return False
            if len(packet_length) < 2:
                packet_length += skt.recv(1)
            # If we didn't get more data and the recv call returned the socket has been closed
            if len(packet_length) < 2:
                self.logger.info('Socket has been closed looking for second byte of packet length')
                return False
            data_chunks.append(packet_length)
            packet_length = int(struct.unpack('H', packet_length)[0])
            self.logger.debug('  length: 0x{:04x}'.format(packet_length))
            # Now get the packet ID
            packet_id = skt.recv(1)
            if packet_id == '':
                self.logger.info('Socket has been closed looking for packet id')
                return False
            data_chunks.append(packet_id)
            packet_id = ord(packet_id)
            self.logger.debug('  ID:     0x{:02x}'.format(packet_id))
            data_remaining = packet_length
            bytes_recvd = 5 # Start with the header received
            while bytes_recvd < (data_remaining):
                data_recvd = skt.recv(min(data_remaining - bytes_recvd, 2048))
                if data_recvd == '':
                    self.logger.info('Socket has been closed receiving data')
                    return False
                data_chunks.append(data_recvd)
                bytes_recvd += len(data_recvd)
                self.logger.debug('  rx data:     {}'.format(''.join('%02x ' % ord(c) for c in data_recvd)))
                self.logger.debug('  bytes_recvd: {}'.format(bytes_recvd))
            # Process the packet
            with self.packet_list_lock:
                if self.packet_list[packet_id] is None:
                    self.logger.warning('Unknown packet received ID = 0x{:02x}'.format(packet_id))
                else:
                    self.packet_list[packet_id].unpack(''.join(data_chunks))
            # Load the received packet on the queue
            self.logger.info('Packet 0x{:02x} recevied'.format(packet_id))
            return self.packet_list[packet_id]
        return None

    def __del__(self):
        self.clientsocket.close()

if __name__ == '__main__':
    import argparse
    import random
    import time

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='Test TCP/IP server')

    parser.add_argument('-p', '--port',
                        help='Port for client to connect to',
                        type=int,
                        default=0)
    parser.add_argument('-a', '--address',
                        help='Network address to connect to',
                        default='')
    parser.add_argument('-n', '--num_clients',
                        help='Number of clients to connect',
                        type=int,
                        default=1)
    parser.add_argument('-l', '--logfile',
                        help='File to log messages to',
                        default=None)
    parser.add_argument('-v', '--verbose',
                        help='Set verbosity level',
                        action='count',
                        default=0)

    args = parser.parse_args()

    # Setup the logger
    if args.logfile is not None:
        logging.basicConfig(filename=args.logfile, format='%(asctime)s: [%(levelname)-7s] %(name)-10s| %(message)s')
    else:
        logging.basicConfig(format='%(asctime)s: [%(levelname)-7s] %(name)-10s| %(message)s')
    root_logger = logging.getLogger()

    if args.verbose > 1:
        root_logger.setLevel(logging.DEBUG)
    elif args.verbose > 0:
        root_logger.setLevel(logging.INFO)

    addr = args.address

    my_packet = packet.Packet(format='f',
                             id=0x01,
                             name='Server Value',
                             element_names=['value'])

    my_clients = []
    for i in range(0, args.num_clients):
        my_clients.append(MyClient(addr, args.port))
        my_clients[-1].add_packet(my_packet)

    loop_count = 0
    while True:
        client_num = 0
        print('Loop count {:04d}'.format(loop_count))
        loop_count += 1
        for my_client in my_clients:
            print('Processing client {:04d}'.format(client_num))
            my_client.process_input(0.1)
            with my_client.packet_list_lock:
                print('Value from server = {}'.format(my_client.packet_list[1].value))
            client_num += 1
