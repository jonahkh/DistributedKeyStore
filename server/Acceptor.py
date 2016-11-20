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
            logger.error('Rejecting proposal {}, sequence number too low {}'.format(data, self.packet_manager.get_time_stamp()))
        else:
            self.sequence_number_manager.set_highest_value('hello', 'world', 'operation')
            packet = self.packet_manager.get_packet('paxos', 'promise', {'sequence_number': self.sequence_number_manager.highest_proposal_number,
                                                                         'value': self.sequence_number_manager.highest_proposed_value})
            self.sequence_number_manager.set(sequence_number)
            self.sequence_number_manager.set_highest_proposed_number(sequence_number)
            logger.error('Accepting proposal {} {}'.format(data, self.packet_manager.get_time_stamp()))
        self.connection.sendall(packet)
        return accept

    def __send_accept(self):
        response = self.connection.recv(BUFFER_SIZE).decode()
        if (isinstance(response, str)):
            response = json.loads(response)
        sequence_number = response['data']
        if (response['status'] == 'reject'):
            logger.error('Accept message rejected by leader {}'.format(self.packet_manager.get_time_stamp()))
            return False
        elif sequence_number < self.sequence_number_manager.highest_proposal_number():
            logger.error('Accept message rejected {} sequence number too low {}'.format(response, self.packet_manager.get_time_stamp()))
            self.connection.sendall(self.packet_manager.get_packet('paxos', 'reject', 'sequence number too low'))
            return False
        else:
            logger.error('Accept message received {} {}'.format(response, self.packet_manager.get_time_stamp()))
            key = response['data']['key']
            value = response['data']['value']
            operation = response['operation']
            self.sequence_number_manager.set_highest_value(key, value, operation)
            self.sequence_number_manager.set(sequence_number)
            self.connection.sendall(self.packet_manager.get_packet('paxos', 'accept', {'key': key, 'value': value}))
            return True

    def __commit(self, data):
        response = self.connection.recv(BUFFER_SIZE).decode()
        if (isinstance(response, str)):
            response = json.loads(response)
        if (response['status'] == 'commit'):
            logger.error('Commit received {}, writing to key store {}'.format(response, self.packet_manager.get_time_stamp()))
            data = response['data']
            key = data['key']
            value = data['value']
            operation = response['operation']
            if ('PUT' == operation):
                self.key_store.put(key, value)
            else:
                self.key_store.delete(key)
            self.sequence_number_manager.set_highest_value()
        else:
            logger.error('Commit rejected {} {}'.format(response, self.packet_manager.get_time_stamp()))