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

class MyClient(object):
    """
    Client template
    """
    def __init__(self, addr, port):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('__init__')

        # Create INET Streaming socket
        self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.clientsocket.connect((addr, port))
        self.logger.info('Client connected to {}'.format(self.clientsocket.getsockname()))

        self.logger.info('Creating data locks')
        self.packet_list_lock = threading.Lock()
        self.packet_list = [None] * packet.PACKET_MAX_ID

        # Non-blocking socket interface
        self.clientsocket.setblocking(0)
        return

    def add_packet(self, pkt):
        self.logger.debug('add_packet({})'.format(repr(pkt)))
        if self.packet_list[pkt.id] is not None:
            self.logger.warning('Packet ID 0x{:02x} already exists'.format(pkt.id))
        with self.packet_list_lock:
            self.packet_list[pkt.id] = pkt

    def process_socket(self, timeout=0.0):
        self.logger.debug('process_socket()')
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
                    self.logger.info('Socket has been closed')
                    socket_closed = True
                    break
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
                self.logger.info('Socket has been closed')
                socket_closed = True
                break
            if len(packet_length) < 2:
                packet_length += skt.recv(1)
            # If we didn't get more data and the recv call returned the socket has been closed
            if len(packet_length) < 2:
                self.logger.info('Socket has been closed')
                socket_closed = True
                break
            data_chunks.append(packet_length)
            packet_length = int(struct.unpack('H', packet_length)[0])
            self.logger.debug('  length: 0x{:04x}'.format(packet_length))
            # Now get the packet ID
            packet_id = skt.recv(1)
            if packet_id == '':
                self.logger.info('Socket has been closed')
                socket_closed = True
                break
            data_chunks.append(packet_id)
            packet_id = ord(packet_id)
            self.logger.debug('  ID:     0x{:02x}'.format(packet_id))
            data_remaining = packet_length
            bytes_recvd = 5 # Start with the header received
            while bytes_recvd < (data_remaining):
                data_recvd = skt.recv(min(data_remaining - bytes_recvd, 2048))
                if data_recvd == '':
                    self.logger.info('Socket has been closed')
                    socket_closed = True
                    break
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

    def __del__(self):
        self.clientsocket.close()

if __name__ == '__main__':
    import argparse
    import random
    import time

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='Test TCP/IP server')

    parser.add_argument('-p', '--port',
                        help='port for server to listen on',
                        type=int,
                        default=0)
    parser.add_argument('-a', '--address',
                        help='Network address to listen on',
                        default='')
    parser.add_argument('-n', '--num_clients',
                        help='Number of clients to connect',
                        type=int,
                        default=1)
    parser.add_argument('-v', '--verbose',
                        help='Set verbosity level',
                        action='count',
                        default=0)

    args = parser.parse_args()

    # Setup the logger
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
            my_client.process_socket(0.1)
            with my_client.packet_list_lock:
                print('Value from server = {}'.format(my_client.packet_list[1].value))
            client_num += 1
