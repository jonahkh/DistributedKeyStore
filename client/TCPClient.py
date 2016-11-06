import socket
import logging
import json
import time
import argparse
import csv
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from client.PacketManager import PacketManager
from client.AbstractClient import AbstractClient
logger = logging.getLogger(__name__)

BUFFER_SIZE = 256
class TCPClient(AbstractClient):
    __metaclass__ = AbstractClient

    def __init__(self, server_address, port):
        super().__init__()
        self.port = port
        self.server_address = (server_address, port)
        self.packet_manager = PacketManager()

    def send_message_tcp(self, operation, key, value=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # sock.settimeout(5)
        print(sock)
        print(self.server_address)
        sock.connect(self.server_address)
        packet = self.packet_manager.get_packet('tcp', operation, key, value)
        message = str(json.dumps(packet)).encode()
        logger.error('Sending request {} {}'.format(message, self.get_time_stamp()))

        sock.sendall(message)
        data = ''
        while True:
            msg = sock.recv(BUFFER_SIZE).decode()
            packet = self.packet_manager.validate_receiving_packet(msg)
            if msg and packet:
                data += msg
            elif msg and not packet:
                logger.error('Received unsolicited response {} {}'.format(msg, self.get_time_stamp()))
            else:
                break
        data = json.loads(data)
        sock.close()
        return data

    def run(self):
        file = open('kvp-operations.txt')
        input = csv.reader(file)
        throughput_begin = time.time()
        self.send_message_tcp('PUT', 'dog', 'puppy')
        self.send_message_tcp('GET', 'dog', 'puppy')
        # for row in input:
        #     before = time.time()
        #     response = self.send_message_tcp(row[0], row[1], row[2])
        #     after = time.time()
        #     call_time = after - before
        #     logger.error('Received message {} that took {} milliseconds {}'.format(response, call_time * 1000, self.get_time_stamp()))
        #     self.timing_information[row[0]].append(call_time * 1000.)
        # throughput_end = time.time()
        # throughput_time = throughput_end - throughput_begin
        # time.sleep(1)
        # throughput = (256 * 150 * .0001) / throughput_time
        # self.get_statistics('TCP')
        # print('Average Throughput: {}'.format(throughput))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--serverAddress', help='Specify the address of the tcp client to connect to', required=True)
    parser.add_argument('-p', '--port', type=int, help='Specify the port of of the server that is listening for tcp packets', required=True)
    args = parser.parse_args()
    tcp_client = TCPClient(args.serverAddress, args.port)
    tcp_client.run()

if __name__ == "__main__":
    main()
