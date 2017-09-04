#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import(print_function)

__version__ = filter(str.isdigit, '$Revision: $')

import socket
import logging
import threading
import select
import time
import packet

SERVER_NETWORK_TIMEOUT = 0.1
SERVER_MAX_PACKET_RATE = 0.1 # Must be greater than 0.01

class MyServer(object):
    """
    Server template
    """
    def __init__(self, addr='', port=0):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('__init__')

        # Create INET Streaming socket
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.serversocket.bind((addr, port))
        self.logger.info('Server bound to {}'.format(self.serversocket.getsockname()))

        self.logger.info('Creating data locks')
        self.status_packet_list_lock = threading.Lock()
        self.status_packet_list_ids = []
        self.packet_list_lock = threading.Lock()
        self.packet_list = [None] * packet.PACKET_MAX_ID
        return

    def add_packet(self, pkt):
        self.logger.debug('add_packet({})'.format(repr(pkt)))
        if self.packet_list[pkt.id] is not None:
            self.logger.warning('Packet ID 0x{:02x} already exists'.format(pkt.id))
        with self.packet_list_lock:
            self.packet_list[pkt.id] = pkt

    def add_status(self, pkt_id):
        self.logger.debug('add_status({})'.format(repr(pkt_id)))
        if self.packet_list[pkt_id] is None:
            self.logger.error('Packet ID 0x{:02x} does not exist'.format(pkt_id))
            raise ValueError
        with self.status_packet_list_lock:
            if pkt_id not in self.status_packet_list_ids:
                self.status_packet_list_ids.append(pkt_id)
                self.logger.info('Packet ID 0x{:02x} added to status'.format(pkt_id))
            else:
                self.logger.warning('Packet ID 0x{:02x} already in status'.format(pkt_id))

    def client_thread(self,skt):
        (client_addr, client_port) = skt.getsockname()
        self.logger.info('Starting client thread for {}:{}'.format(client_addr, client_port))
        # Setup the socket
        socket_closed = False
        next_packet_time = round(time.time() + SERVER_MAX_PACKET_RATE, 2)
        skt.settimeout(SERVER_NETWORK_TIMEOUT)
        # Make local copy of default global variables
        # Loop until the socket is closed by the client
        while not socket_closed:
            # Send telemetry packets based on subscription interval
            if time.time() > next_packet_time:
                next_packet_time = round(time.time() + SERVER_MAX_PACKET_RATE, 2)
                self.logger.debug('Next packet time: {}'.format(next_packet_time))
                with self.status_packet_list_lock:
                    for status_packet_id in self.status_packet_list_ids:
                        bytes_sent = 0
                        with self.packet_list_lock:
                            packet_data = self.packet_list[status_packet_id].pack()
                        while bytes_sent < len(packet_data):
                            sent = skt.send(packet_data[bytes_sent:])
                            if sent == 0:
                                self.logger.info('Sending socket has been closed')
                                socket_closed = True
                                break
                            bytes_sent += sent

            # Wait for commands to be received
            try:
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
                    self.logger.debug('  rx:     0x{:02x}'.format(int(data_byte)))
                    if data_byte == packet.PACKET_START_BYTES[start_byte_index]:
                        data_chunks.append(data_byte)
                        start_byte_index += 1
                    else:
                        self.logger.info('  Start byte expected but not received')
                        data_chunks = []
                        start_byte_index = 0
                    if start_byte_index > 1:
                        self.logger.debug('  Start byte found')
                        start_byte_found = True
                if socket_closed:
                    break
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
                self.logger.debug('  length: 0x{:04x}'.format(int(packet_length)))
                # Now get the packet ID
                packet_id = skt.recv(1)
                if packet_id == '':
                    self.logger.info('Socket has been closed')
                    socket_closed = True
                    break
                data_chunks.append(packet_id)
                packet_id = int(packet_id)
                self.logger.debug('  ID:     0x{:02x}'.format(packet_id))
                data_chunks.append(packet_length)
                data_remaining = int(packet_length) - 5
                bytes_recvd = 0
                while bytes_recvd < (data_remaining):
                    data_recvd = skt.recv(min(data_remaining - bytes_recvd, 2048))
                    if data_recvd == '':
                        self.logger.info('Socket has been closed')
                        socket_closed = True
                        break
                    data_chunks.append(data_recvd)
                    bytes_recvd += len(data_recvd)
                # Process the packet
                with self.packet_list_lock:
                    self.packet_list[packet_id].unpack(''.join(data_chunks))
                # Load the received packet on the queue
                self.logger.info('Packet 0x{:02x} recevied'.format(packet_id))
            except socket.timeout:
                self.logger.debug('Socket receive timeout')
        self.logger.info('client_tread exitting')

    def start(self):
        self.logger.debug('Server started')
        self.serversocket.listen(5)
        while True:
            (clientsocket, address) = self.serversocket.accept()
            self.logger.info('Client connected from {}'.format(address))
            d = threading.Thread(target=self.client_thread, args=(clientsocket,))
            d.setDaemon(True)
            d.start()

    def __del__(self):
        self.serversocket.close()

if __name__ == '__main__':
    import argparse
    import random
    import time
    import packet

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='Test TCP/IP server')

    parser.add_argument('-p', '--port',
                        help='port for server to listen on',
                        default=0)
    parser.add_argument('-i', '--interface',
                        help='Network interface to listen on',
                        default=None)
    parser.add_argument('-a', '--address',
                        help='Network address to listen on',
                        default='')
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

    addr = args.address

    if args.interface is not None:
        # Interface selection takes priorit over address
        addr = args.interface

    my_packet = packet.Packet(format='f',
                             id=0x01,
                             name='Server Value',
                             element_names=['value'])

    my_packet_2 = packet.Packet(format='f',
                                id=0x02,
                                name='Server Value 2',
                                element_names=['value_2'])

    my_server = MyServer(addr, args.port)
    print('Server bound to {}'.format(my_server.serversocket.getsockname()))
    my_server.add_packet(my_packet)
    my_server.add_packet(my_packet_2)
    my_server.add_status(1)
    my_server.add_status(1)
    my_server.add_status(2)

    server_thread = threading.Thread(target=my_server.start)
    server_thread.setDaemon(True)
    server_thread.start()

    while True:
        # Wait for a random amount of time, and update data with a new random value to be sent by
        # the server
        delay_time = random.uniform(0, 3)
        root_logger.info('Delaying {}'.format(delay_time))
        time.sleep(delay_time)
        with my_server.packet_list_lock:
            my_server.packet_list[1].value = random.uniform(0,100)
            my_server.packet_list[2].value_2 = random.uniform(0,100)
            print('Server new value = {}'.format(my_server.packet_list[1].value))
