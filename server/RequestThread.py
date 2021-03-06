import threading
import json
import logging
import socket
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from server.Proposer import Proposer
from server.Acceptor import Acceptor

logger = logging.getLogger(__name__)
BUFFER_SIZE = 256

class RequestThread(threading.Thread):
    def __init__(self, queue, key_store, thread_lock, packet_manager, server_addresses, sequence_number_manager):
        threading.Thread.__init__(self, daemon=True)
        self.request_queue = queue
        self.thread_lock = thread_lock
        self.key_store = key_store
        self.server_addresses = server_addresses[0]
        self.port = server_addresses[1]
        self.packet_manager = packet_manager
        self.server_address = socket.gethostbyname(socket.gethostname())
        self.sequence_number = sequence_number_manager

    def __handle_request(self, connection, client_address):
        msg = connection.recv(BUFFER_SIZE).decode()
        logger.error('Query received: {} from INET: {}, Port: {} {}'.format(msg, client_address[0], client_address[1],
                                                                   self.packet_manager.get_time_stamp()))
        data = json.loads(msg)
        valid_packet = self.packet_manager.is_valid_packet(data)
        if ('tcp' == data['protocol'] and self.packet_manager.is_valid_tcp_packet(data)):         # Message from client
            if (data['operation'] == 'GET'):
                response = self.key_store.get(data['data']['key'])
            else:
                response = Proposer(self.sequence_number, self.packet_manager, self.server_address, self.server_addresses, self.port).propose(data)
            logger.error('Query response: {} {}'.format(response, self.packet_manager.get_time_stamp()))
            connection.sendall(response)
        elif ('paxos' == data['protocol'] and valid_packet):
            Acceptor(self.key_store, self.packet_manager, connection, client_address, self.sequence_number).accept(data)
        else:
            response = self.packet_manager.get_packet('tcp', 'failure', 'Not a valid packet')
            logger.error('Received malformed request from {}: {} {}'.format(client_address[0], client_address[1],
                                                              self.packet_manager.get_time_stamp()))
            connection.sendall(response)
        connection.close()

    def run(self):
        while True:
            request = self.request_queue.get()
            self.__handle_request(request['connection'], request['client_address'])