import threading
import time
import json
import logging
import socket
import os
import sys
import concurrent.futures
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from enum import Enum
from server.PacketManager import PacketManager

logger = logging.getLogger(__name__)
BUFFER_SIZE = 256

class Request(Enum):
    PUT = "PUT"
    GET = "GET"
    DELETE = "DELETE"

# packet_manager = PacketManager()
sequence_number_manager = {}

class RequestThread(threading.Thread):
    def __init__(self, queue, key_store, thread_lock, packet_manager, server_addresses):
        threading.Thread.__init__(self, daemon=True)
        self.request_queue = queue
        self.key_store = key_store
        self.thread_lock = thread_lock
        self.server_addresses = server_addresses[0]
        self.port = server_addresses[1]
        self.packet_manager = packet_manager


    def __tcp_protocol(self, connection, client_address):
        # print('connection: {}'.format(connection))
        msg = connection.recv(BUFFER_SIZE).decode()
        logger.error(
            'Query received: {} from INET: {}, Port: {} {}'.format(msg, client_address[0], client_address[1],
                                                                   self.packet_manager.get_time_stamp()))
        data = json.loads(msg)
        if ('tcp' == data['protocol'] and self.packet_manager.is_valid_tcp_packet(data)):         # Message from client
            response = self.__get_data(data)
            logger.error('Query response: {} {}'.format(response, self.packet_manager.get_time_stamp()))
        elif ('2pc' == data['protocol'] and self.packet_manager.is_valid_2pc_packet(data)):       # Message from another node
            response = self.__handle_2PC(connection, client_address)
            logger.error('Query response: {} {}'.format(response, self.packet_manager.get_time_stamp()))
        else:
            response = self.packet_manager.get_packet('tcp', 'failure', 'Not a valid packet')
            logger.error(
                'Received malformed request from {}: {} {}'.format(client_address[0], client_address[1],
                                                              self.packet_manager.get_time_stamp()))
        connection.sendall(response)
        connection.close()
        return response

    def __handle_2PC(self, connection, client_address):
        ack_packet = self.packet_manager.get_packet('2pc', 'ack', 'waiting for commit')
        logger.error('Sending acknowledgment {} to {} {}'.format(ack_packet, client_address[0], self.packet_manager.get_time_stamp()))
        connection.send_all(ack_packet)
        response = connection.recv(BUFFER_SIZE).decode()
        commit_message = json.loads(response)
        if (self.packet_manager.is_valid_2pc_packet(commit_message)):
            if (commit_message['status'] == 'success'):
                logger.error('Acknowledgment received {} from {} {}'.format(commit_message, client_address[0], self.packet_manager.get_time_stamp()))
                data = self.__get_data(commit_message)
            else:
                logger.error(
                    'Aborting request from {}:{} {}'.format(client_address[0], client_address[1],
                                                                      self.packet_manager.get_time_stamp()))
        else:
            logger.error(
                'Received malformed request from {}: {} {}'.format(client_address[0], client_address[1],
                                                                  self.packet_manager.get_time_stamp()))
        return self.packet_manager.get_packet('tcp', 'success', 'who needs data?')

            
    def __get_data(self, data):
        key = data['data']['key']
        value = data['data']['value']
        operation = data['operation']
        response = None
        commit_message = True
        if (operation == Request.GET.name):
            response = self.get(key)
        else:
            if ('tcp' in data['protocol']):
                commit_message = self.__coordinator_handler(key, value, operation)
            if (commit_message and operation == Request.DELETE.name):
                response = self.delete(key)
            elif (commit_message and operation == Request.PUT.name):
                response = self.put(key, value)
        return response
    
    def __coordinator_handler(self, key, value, operation):
        # request_list = [
        #     '192.168.1.138'
        # ]
        request_list = self.server_addresses
        response_list = []
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                print('serving requests to other servers')
                for server in self.server_addresses:
                    response_list.append(executor.submit(self.__phase_1, server, request_list))
                    # if (server is not socket.gethostbyname(socket.gethostname())):
                    # request_list[server] = {'socket': sock, 'ack_received': False}
                print('all requests sent')
                while request_list:
                    pass
                # time.sleep(5)
            print('here')
        except Exception as e:
            print(e)

    def __phase_1(self, server_address, request_list):
        # print('Sending to {}'.format(server_address))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # print('sock {}'.format(sock))
        sock.connect((server_address, self.port))
        packet = self.packet_manager.get_packet('2pc', 'requesting ack', 'requesting ack')
        print('sending packet {}'.format(packet))
        sock.settimeout(1000)
        sock.sendall(packet)

        # print('packet sent {} '.format(packet))
        msg = sock.recv(BUFFER_SIZE).decode()
        request_list.pop(server_address)
        print('msg: '.format(msg))


    def run(self):
        while True:
            request = self.request_queue.get()
            # print('request: {}'.format(request))
            response = self.__tcp_protocol(request['connection'], request['client_address'])
            print(response)

    def delete(self, key):
        status = 'failure'
        response = None
        self.thread_lock.acquire()
        if key in self.key_store:
            self.key_store.pop(key)
            status = 'success'
        else:
            response = 'Key not found'
        self.thread_lock.release()
        return self.packet_manager.get_packet('tcp', status, response)

    def get(self, key):
        status = 'failure'
        self.thread_lock.acquire()
        if key in self.key_store:
            response = self.key_store.get(key)
            status = 'success'
        else:
            response = 'Key not found'
        self.thread_lock.release()
        return self.packet_manager.get_packet('tcp', status, response)

    def put(self, key, value):
        self.thread_lock.acquire()
        self.key_store[key] = value
        self.thread_lock.release()
        return self.packet_manager.get_packet('tcp', 'success', None)
