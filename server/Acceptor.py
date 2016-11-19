import json
import logging

logger = logging.getLogger(__name__)

BUFFER_SIZE = 256

class Acceptor():
    def __init__(self, key_store, packet_manager, connection, client_address, sequence_number_manager):
        self.key_store = key_store
        self.packet_manager = packet_manager
        self.connection = connection
        self.client_address = client_address
        self.sequence_number_manager = sequence_number_manager

    def accept(self, data):
        sequence_number = data['data']
        promise = self.__send_promise(data, sequence_number)
        if (promise):
            response = self.__send_accept()
            if (response):
                self.__commit(response)



    def __send_promise(self, data, sequence_number):
        accept = True
        if (self.sequence_number_manager.get_sequence_number() > sequence_number):
            packet = self.packet_manager.get_packet('paxos', 'reject', 'lower sequence number')
            accept = False
        else:
            packet = self.packet_manager.get_packet('paxos', 'promise', {'sequence_number': self.sequence_number_manager.highest_proposal_number,
                                                                         'value': self.sequence_number_manager.highest_proposed_value})
            self.sequence_number_manager.set(sequence_number)
            self.sequence_number_manager.set_highest_proposed_number(sequence_number)
        self.connection.sendall(packet)
        return accept

    def __send_accept(self):
        response = self.connection.recv(BUFFER_SIZE).decode()
        sequence_number = response['data']
        if (response['status'] == 'reject'):
            return False
        elif sequence_number < self.sequence_number_manager.highest_proposal_number():
            self.connection.sendall(self.packet_manager.get_packet('paxos', 'reject', 'sequence number too low'))
            return False
        else:
            key = response['data']['key']
            value = response['data']['value']
            operation = response['operation']
            self.sequence_number_manager.set_highest_value(key, value)
            self.sequence_number_manager.set(sequence_number)
            self.connection.sendall(self.packet_manager.get_packet('paxos', 'accept', {'key': key, 'value': value}))
            return key, value, operation

    def __commit(self, data):
        response = self.connection.recv(BUFFER_SIZE).decode()
        if (response['status']['commit']):
            data = response['data']
            key = data['key']
            value = data['value']
            operation = response['operation']
            if ('PUT' == operation):
                self.key_store.put(key, value)
            else:
                self.key_store.delete(key)
            self.sequence_number_manager.set_highest_value()

    # def __handle_2PC(self, connection, client_address):
    #     ack_packet = self.packet_manager.get_packet('2pc', 'ack', 'waiting for commit')
    #     logger.error('Sending acknowledgment {} to {} {}'.format(ack_packet, client_address[0], self.packet_manager.get_time_stamp()))
    #     connection.sendall(ack_packet)
    #     if (client_address[0] != self.server_address):  # Only acknowledge own request, don't commit write (client address on calling thread)
    #         response = connection.recv(BUFFER_SIZE).decode()
    #         logger.error('Received response {} from: {}'.format(response, client_address))
    #         commit_message = json.loads(response)
    #         if (self.packet_manager.is_valid_2pc_packet(commit_message)):   # Execute if successful commit message (all servers responsive)
    #             if (commit_message['status'] == 'success'):
    #                 logger.error('Commit message received {} from {} {}'.format(commit_message, client_address[0], self.packet_manager.get_time_stamp()))
    #                 self.__get_data(commit_message)
    #             else:
    #                 logger.error('Aborting request from {}:{} {}'.format(client_address[0], client_address[1],
    #                                                                       self.packet_manager.get_time_stamp()))
    #         else:
    #             logger.error('Received malformed request from {}: {} {}'.format(client_address[0], client_address[1],
    #                                                                   self.packet_manager.get_time_stamp()))