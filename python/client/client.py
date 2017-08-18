#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import(print_function)

__version__ = filter(str.isdigit, '$Revision: $')

import socket
import logging
import threading

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
        return

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

    for i in range(0, args.num_clients - 1):
        my_client = MyClient(addr, args.port)
