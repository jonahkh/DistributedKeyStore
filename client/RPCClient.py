import argparse
import csv
import time
import logging
import socket
from xmlrpc.client import ServerProxy
from client.PacketManager import PacketManager
from client.AbstractClient import AbstractClient

logger = logging.getLogger(__name__)

class RPCClient(AbstractClient):
    __metaclass__ = AbstractClient

    def __init__(self, server_address, port):
        super().__init__()
        self.server_address = server_address
        self.port = port
        self.packet_manager = PacketManager()

    def run(self):
        file = open('kvp-operations.txt')
        input = csv.reader(file)
        proxy = ServerProxy('http://{}:{}'.format(self.server_address, self.port))
        throughput_begin = time.time()
        for row in input:
            before = time.time()
            packet = self.packet_manager.get_packet('rpc', row[0], row[1], row[2], inet=socket.gethostbyname(socket.gethostname()))
            response = proxy.rpc_request(packet)
            after = time.time()
            call_time = after - before
            logger.error('Received message {} that took {} milliseconds {}'.format(response, call_time * 1000, self.get_time_stamp()))
            # Record time for each operation type in milliseconds
            self.timing_information[row[0]].append(call_time * 1000.)
        # Delay to allow any remaining messages to be received
        throughput_end = time.time()
        throughput_time = throughput_end - throughput_begin
        time.sleep(1)
        self.get_statistics('RPC')
        throughput = (256 * 150 * .0001) / throughput_time
        print('Average Throughput: {}'.format(throughput))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--serverAddress', type=int, help='Specify the address of the udp client to connect to')
    parser.add_argument('-p', '--port', type=int, help='Specify the port of of the server that is listening for udp packets')
    args = parser.parse_args()
    rpc_client = RPCClient(args.serverAddress, args.port)
    rpc_client.run()

if __name__ == "__main__":
    main()