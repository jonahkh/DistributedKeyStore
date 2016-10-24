import threading
import time
import json
import logging
import socket
from enum import Enum
from server.PacketManager import PacketManager

logger = logging.getLogger(__name__)
BUFFER_SIZE = 256

class Request(Enum):
    PUT = "PUT"
    GET = "GET"
    DELETE = "DELETE"

key_store = {}
thread_lock = threading.Lock()
packet_manager = PacketManager()
sequence_number_manager = {}

class RequestThread(threading.Thread):
    def __init__(self, connection, client_address, protocol, port=None):
        threading.Thread.__init__(self)
        self.connection = connection
        self.client_address = client_address
        self.protocol = protocol
        self.port = port
        self.response = None

    def __is_valid_packet(self, packet, protocol):
        return ('protocol' in packet and protocol == self.protocol
                and 'operation' in packet and self.__is_valid_operation(packet.get('operation'))
                and 'data' in packet
                and 'key' in packet.get('data')
                and 'value' in packet.get('data'))

    def __tcp_protocol(self):
        msg = self.connection.recv(BUFFER_SIZE).decode()
        logger.error(
            'Query received: {} from INET: {}, Port: {} {}'.format(msg, self.client_address[0], self.client_address[1],
                                                                   self.__get_time_stamp()))
        data = json.loads(msg)
        response = None
        if (self.__is_valid_packet(data, data.get('protocol'))):
            response = self.__get_data(data)
            self.connection.sendall(response.encode())
            logger.error('Query response: {} {}'.format(response, self.__get_time_stamp()))
        else:
            self.connection.sendall(packet_manager.get_packet('tcp', 'failure', 'Not a valid packet'))
            logger.error(
                'Received malformed request from {}:{} {}'.format(self.client_address[0], self.client_address[1],
                                                                  self.__get_time_stamp()))
        self.connection.close()
        return response

    def __is_valid_operation(self, operation):
        return operation == Request.PUT.name or operation == Request.DELETE.name or operation == Request.GET.name

    def __get_time_stamp(self):
        return 'at local time: {}, system time: {}'.format(time.asctime(), time.time())

    def __udp_protocol(self):
        logger.error('Query received: {} from INET: {}, Port: {} {}'.format(self.connection, self.client_address[0],
                                                                            self.client_address[1],
                                                                            self.__get_time_stamp()))
        data = json.loads(self.connection.decode())
        response = None
        if (self.__is_valid_packet(data, data.get('protocol'))):
            # Sequence numbers are tracked to guarantee ordering
            client_sequence_number = data.get('sequence_number')
            if (self.client_address[0] not in sequence_number_manager):
                sequence_number_manager[self.client_address[0]] = {'sequence_number': client_sequence_number}
            if (sequence_number_manager[self.client_address[0]]['sequence_number'] > client_sequence_number):
                print('duplicate message received')
                response = sequence_number_manager[self.client_address[0]]['last_message']
            else:
                response = self.__get_data(data)
                sequence_number_manager[self.client_address[0]]['last_message'] = response
                sequence_number_manager[self.client_address[0]]['sequence_number'] = client_sequence_number + 1
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            logger.error('Query response: {} {}'.format(response, self.__get_time_stamp()))
            sock.sendto(response.encode(), (self.client_address[0], self.port + 1))
            sock.close()

        else:
            logger.error(
                'Received malformed request from {}:{} {}'.format(self.client_address[0], self.client_address[1],
                                                                  self.__get_time_stamp()))
        return response

    def get_result(self):
        logger.error('Query response: {} {}'.format(self.response, self.__get_time_stamp()))
        return self.response

    def __get_data(self, data):
        key = data['data']['key']
        value = data['data']['value']
        operation = data['operation']
        response = None
        if (operation == Request.DELETE.name):
            response = self.delete(key)
        elif (operation == Request.GET.name):
            response = self.get(key)
        elif (operation == Request.PUT.name):
            response = self.put(key, value)
        return response

    def run(self):
        response = None
        if (self.protocol is 'tcp'):
            response = self.__tcp_protocol()
        elif (self.protocol is 'udp'):
            response = self.__udp_protocol()
        elif (self.protocol is 'rpc'):
            logger.error('Query received: {} from INET: {} Port: {} {}'.format(self.connection, self.connection['INET'],
                                                                               self.port, self.__get_time_stamp()))

            if (self.__is_valid_packet(self.connection, self.connection.get('protocol'))):
                response = self.__get_data(self.connection)
            else:
                logger.error(
                    'Received malformed request from {}:{} {}'.format(self.client_address[0], self.client_address[1],
                                                                      self.__get_time_stamp()))
        self.response = response

    def delete(self, key):
        status = 'failure'
        response = None
        thread_lock.acquire()
        if key in key_store:
            key_store.pop(key)
            status = 'success'
        else:
            response = 'Key not found'
        thread_lock.release()
        return json.dumps(packet_manager.get_packet(self.protocol, status, response))

    def get(self, key):
        status = 'failure'
        thread_lock.acquire()
        if key in key_store:
            response = key_store.get(key)
            status = 'success'
        else:
            response = 'Key not found'
        thread_lock.release()
        return json.dumps(packet_manager.get_packet(self.protocol, status, response))

    def put(self, key, value):
        thread_lock.acquire()
        key_store[key] = value
        thread_lock.release()
        return json.dumps(packet_manager.get_packet(self.protocol, 'success', None))
