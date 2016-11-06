import time
import json
from enum import Enum

class Request(Enum):
    PUT = "PUT"
    GET = "GET"
    DELETE = "DELETE"

class PacketManager():
    def get_packet(self, protocol, status, data):
        return json.dumps({'protocol': protocol, 'status': status, 'data': data}).encode()


    def is_valid_packet(self, packet):
        return ('protocol' in packet
                and 'operation' in packet and self.is_valid_operation(packet.get('operation'))
                and 'data' in packet)
                # and 'key' in packet.get('data')
                # and 'value' in packet.get('data'))

    def is_valid_operation(self, operation):
        return operation == Request.PUT.name or operation == Request.DELETE.name or operation == Request.GET.name

    def get_time_stamp(self):
        return 'at local time: {}, system time: {}'.format(time.asctime(), time.time())
