#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import(print_function)

__version__ = filter(str.isdigit, '$Revision: $')

import socket
import logging
import threading

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
        return

    def client_thread(self,skt):
        (client_addr, client_port) = skt.getsockname()
        self.logger.info('Starting client thread for {}:{}'.format(client_addr, client_port))
        # Make local copy of default global variables
        # Loop until the socket is closed by the client
        # Send telemetry packets based on subscription interval
        # Use select statement to wait for commands to be received

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

    my_server = MyServer(addr, args.port)

    server_thread = threading.Thread(target=my_server.start)
    server_thread.setDaemon(True)
    server_thread.start()

    while True:
        # Wait for a random amount of time, and update data with a new random value to be sent by
        # the server
        delay_time = random.uniform(0, 3)
        root_logger.info('Delaying {}'.format(delay_time))
        time.sleep(delay_time)
        new_value = random.uniform(0,100)
        print('Server new value = {}'.format(new_value))
