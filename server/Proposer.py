import os
import sys
import logging
import socket
import time
import copy
import json
import concurrent.futures

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

BUFFER_SIZE = 256
QUORUM = 3

class Proposer():
    def __init__(self, sequence_number_manager, packet_manager, server_address, server_addresses, port):
        self.sequence_number = sequence_number_manager
        self.response_list = {}
        self.packet_manager = packet_manager
        self.server_address = server_address
        self.server_addresses = server_addresses
        self.port = port

    def propose(self, data):
        sequence_number = self.sequence_number.increment()
        key = data['data']['key']
        value = data['data']['value']
        operation = data['operation']
        commit_message = True
        response_list = self.__prepare_propose_commit(sequence_number, key, value, operation)
        acceptors = None
        if len(response_list) >= QUORUM:
            self.__accept(response_list, key, value, operation)
        else:
            logger.error('Quorum not received, rejecting promises')
        return self.packet_manager.get_packet('tcp', 'success', 'success')
    # Phase 1
    def __prepare_propose_commit(self, sequence_number, key, value, operation):
        request_list = copy.copy(self.server_addresses)
        response_list = []
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                for server in self.server_addresses:
                    response_list.append(executor.submit(self.__propose_commit, server, request_list, sequence_number))
                beg_time = time.time()
                while len(request_list) > QUORUM and time.time() - beg_time < 1:  # Timeout after 5 seconds
                    pass
                executor.shutdown(wait=False)
        except ConnectionError as e:
            logger.error('failed to connect to server {}'.format(e))
        except Exception as e:
            print(e)

        # packet = self.packet_manager.get_packet('2pc', 'success', {'key': key, 'value': value}, operation) \
        #     if not request_list else self.packet_manager.get_packet('2pc', 'failure', 'abort')
        # self.__send_commit(packet, response_list)
        # return not request_list
        return response_list

    def __propose_commit(self, server_address, request_list, sequence_number):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        count = 0
        sock.settimeout(.5)
        while True:
            try:
                sock.connect((server_address, self.port))
                break
            except:
                count += 1
                if (count > 5): # timeout after 5 tries
                    sock.close()
                    return
        packet = self.packet_manager.get_packet('paxos', 'prepare commit', sequence_number)
        logger.error('Sending prepare commit {} to {}'.format(packet, server_address))
        sock.sendall(packet)
        msg = sock.recv(BUFFER_SIZE).decode()
        if (isinstance(msg, str)):
            msg = json.loads(msg)
        logger.error('Promise {} received from {}'.format(msg, server_address))

        if (msg['status'] == 'promise'):
            request_list.remove(server_address)
        return sock, msg

    # Phase 2
    def __accept(self, response_list, key, value, operation):
        values = []
        value_count = {}
        for response in response_list:
            response = response.result()
            msg = response[1]
            if (isinstance(msg, str)):
                msg = json.loads(msg)
            data = msg['data']
            print('msg: {}'.format(msg))
            if data['value'] in values:
                value_count[data['value']] += 1
            else:
                print('value count: {}'.format(value_count))
                print('values: {}'.format(values))
                print('data: {}'.format(data))
                values.append(data['value'])
                value_count[data['value']] = 1
        highest_value = values[0]
        highest_count = value_count[values[0]]
        print('Highest value: {}'.format(highest_value))
        for value in values:
            if (value_count[value] > highest_count):
                highest_count = value_count[value]
                highest_value = value
        accept_list = []
        if not highest_value:
            packet = self.packet_manager.get_packet('paxos', 'accept', {'key': key, 'value': value}, operation)
        else:
            packet = self.packet_manager.get_packet('paxos', 'accept', {'key': highest_value['key'], 'value': highest_value['value']}, highest_value['operation'])
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for response in response_list:
                accept_list.append(executor.submit(self.__send_accept, response.result()[0], packet))


    def __send_accept(self, client_address, packet):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        count = 0
        sock.settimeout(.5)
        while True:
            try:
                sock.connect((server_address, self.port))
                break
            except:
                count += 1
                if (count > 5): # timeout after 5 tries
                    sock.close()
                    return
        packet = self.packet_manager.get_packet('paxos', 'prepare commit', sequence_number)
        logger.error('Sending prepare commit {} to {}'.format(packet, server_address))
        sock.sendall(packet)
        msg = sock.recv(BUFFER_SIZE).decode()
        logger.error('Promise {} received from {}'.format(msg, server_address))

    # Phase 3
    def __send_commit(self, packet, response_list):
        for response in response_list:
            sock = response.result()
            if (sock):
                peer_name = sock.getpeername()
                if (self.server_address != peer_name[0]):
                    sock.sendall(packet)
                sock.close()
