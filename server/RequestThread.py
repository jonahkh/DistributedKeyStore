import threading
import json
import logging
import socket
import os
import sys
import copy
import concurrent.futures
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)
BUFFER_SIZE = 256

class RequestThread(threading.Thread):
    def __init__(self, queue, key_store, thread_lock, packet_manager, server_addresses):
        threading.Thread.__init__(self, daemon=True)
        self.request_queue = queue
        self.key_store = key_store
        self.thread_lock = thread_lock
        self.server_addresses = server_addresses[0]
        self.port = server_addresses[1]
        self.packet_manager = packet_manager
        self.server_address = socket.gethostbyname(socket.gethostname())

    def __tcp_protocol(self, connection, client_address):
        msg = connection.recv(BUFFER_SIZE).decode()
        logger.error(
            'Query received: {} from INET: {}, Port: {} {}'.format(msg, client_address[0], client_address[1],
                                                                   self.packet_manager.get_time_stamp()))
        data = json.loads(msg)
        if ('tcp' == data['protocol'] and self.packet_manager.is_valid_tcp_packet(data)):         # Message from client
            response = self.__get_data(data)
            logger.error('Query response: {} {}'.format(response, self.packet_manager.get_time_stamp()))
            connection.sendall(response)
        elif ('2pc' == data['protocol'] and self.packet_manager.is_valid_2pc_packet(data)):       # Message from another node
            response = self.__handle_2PC(connection, client_address)
            # logger.error('Query response: {} {}'.format(response, self.packet_manager.get_time_stamp()))
        else:
            response = self.packet_manager.get_packet('tcp', 'failure', 'Not a valid packet')
            logger.error(
                'Received malformed request from {}: {} {}'.format(client_address[0], client_address[1],
                                                              self.packet_manager.get_time_stamp()))
            connection.sendall(response)
        connection.close()

    def __handle_2PC(self, connection, client_address):
        ack_packet = self.packet_manager.get_packet('2pc', 'ack', 'waiting for commit')
        logger.error('Sending acknowledgment {} to {} {}'.format(ack_packet, client_address[0], self.packet_manager.get_time_stamp()))
        connection.sendall(ack_packet)
        if (client_address[0] != self.server_address):
            response = connection.recv(BUFFER_SIZE).decode()
            logger.error('Received response {} from: {}'.format(response, client_address))
            commit_message = json.loads(response)
            if (self.packet_manager.is_valid_2pc_packet(commit_message)):
                if (commit_message['status'] == 'success'):
                    logger.error('Commit message received {} from {} {}'.format(commit_message, client_address[0], self.packet_manager.get_time_stamp()))
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
        if (operation == 'GET'):
            response = self.get(key)
        else:
            if ('tcp' in data['protocol']):
                print('passing to coordinator')
                commit_message = self.__coordinator_handler(key, value, operation)
            if (commit_message and operation == 'DELETE'):
                response = self.delete(key)
            elif (commit_message and operation == 'PUT'):
                response = self.put(key, value)
        return response
    
    def __coordinator_handler(self, key, value, operation):
        request_list = copy.copy(self.server_addresses)
        response_list = []
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                for server in self.server_addresses:
                    response_list.append(executor.submit(self.__phase_1, server, request_list))
                beg_time = time.time()
                while request_list and time.time() - beg_time < 5:  # Timeout after 5 seconds
                    pass
                executor.shutdown(wait=False)
        except ConnectionError as e:
            print('failed to connect to server {}'.format(e))
        except Exception as e:
            print(e)
        packet = self.packet_manager.get_packet('2pc', 'success', {'key': key, 'value': value}, operation) \
            if not request_list else self.packet_manager.get_packet('2pc', 'failure', 'abort')
        self.__send_commit(packet, response_list)
        return request_list

    def __send_commit(self, packet, response_list):
        for response in response_list:
            sock = response.result()
            peer_name = sock.getpeername()
            if (self.server_address != peer_name[0]):
                sock.sendall(packet)
            sock.close()

    def __phase_1(self, server_address, request_list):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect((server_address, self.port))
        packet = self.packet_manager.get_packet('2pc', 'requesting ack', 'requesting ack')
        while True:
            try:
                sock.sendall(packet)
                msg = sock.recv(BUFFER_SIZE).decode()
                logger.error('Ack {} received from {}'.format(msg, server_address))
                request_list.remove(server_address)
                break
            except Exception as e:
                print(e)
        return sock


    def run(self):
        while True:
            request = self.request_queue.get()
            self.__tcp_protocol(request['connection'], request['client_address'])

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
