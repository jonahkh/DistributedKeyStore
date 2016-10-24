class PacketManager():
    def get_packet(self, protocol, status, data):
        return {'protocol': protocol, 'status': status, 'data': data}