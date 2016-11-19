import time
import json
"""
    Class for managing server packets.
"""
class PacketManager():
    def get_packet(self, protocol, status, data, operation=None):
        return json.dumps({'protocol': protocol, 'status': status, 'data': data, 'operation': operation}).encode()

    def is_valid_tcp_packet(self, packet):
        return ('protocol' in packet
                and 'operation' in packet and self.is_valid_operation(packet.get('operation'))
                and 'data' in packet
                and 'key' in packet.get('data')
                and 'value' in packet.get('data'))

    def is_valid_packet(self, packet):
        return ('protocol' in packet
                and 'data' in packet
                and 'status' in packet)

    def is_valid_operation(self, operation):
        return operation == 'PUT' or operation == 'DELETE' or operation == 'GET'

    def get_time_stamp(self):
        return 'at local time: {}, system time: {}'.format(time.asctime(), time.time())