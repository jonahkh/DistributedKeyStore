class PacketManager():
    def get_packet(self, protocol, operation, key, value, sequence_number=None, inet=None):
        packet =  {'protocol': protocol, 'operation': operation, 'data': {
            'key': key, 'value': value
        }}
        if sequence_number:
            packet['sequence_number'] = sequence_number
        if inet:
            packet['INET'] = inet
        return packet

    def validate_receiving_packet(self, packet):
        return ('protocol' in packet
            and 'status' in packet
            and 'data' in packet)