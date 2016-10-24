import socket
import json
import time
import argparse
import csv
import logging
from client.PacketManager import PacketManager
from client.AbstractClient import AbstractClient
logger = logging.getLogger(__name__)

BUFFER_SIZE = 256
RETRY_LIMIT = 20
TIMEOUT_TIME = .05
class UDPClient(AbstractClient):
    __metaclass__ = AbstractClient

    def __init__(self, server_address, port):
        super().__init__()
        self.port = port
        self.server_address = (server_address, port)
        self.packet_manager = PacketManager()

    # Protocol code
    def send_message_udp(self, operation, key, sequence_number, value=None):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            value = None if not value else value
            packet = self.packet_manager.get_packet('udp', operation, key, value, sequence_number)
            message = str(json.dumps(packet)).encode()
            logger.error('Sending request {} {}'.format(message, self.get_time_stamp()))
            sock.sendto(message, self.server_address)
            sock.close()
        except Exception as e:
            print(e)

    def run(self):
        file = open('kvp-operations.txt')
        input = csv.reader(file)
        sequence_number = 1
        throughput_begin = time.time()
        for row in input:
            tries = 0
            before = time.time()
            while True:
                tries += 1
                if (tries > RETRY_LIMIT):
                    logger.error('Server unresponsive after {} tries {}'.format(RETRY_LIMIT, self.get_time_stamp()))
                    sequence_number += 1
                    break
                self.send_message_udp(row[0], row[1], sequence_number, row[2])
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(TIMEOUT_TIME)
                receiving_port = self.port + 1 if self.port < 65535 else self.port - 1
                try:
                    sock.bind(('localhost', receiving_port))
                    data, addr = sock.recvfrom(BUFFER_SIZE)
                    data = data.decode()
                    if (self.packet_manager.validate_receiving_packet(data)):
                        after = time.time()
                        call_time = after - before
                        logger.error(
                            'Received message {} that took {} milliseconds {}'.format(data, call_time * 1000,
                                                                                      self.get_time_stamp()))
                        self.timing_information[row[0]].append(call_time * 1000)
                        break
                    else:
                        logger.error(
                            'Received unsolicited response acknowledging unknown PUT/GET/DELETE with an invalid key {}'.format(
                                 self.get_time_stamp()))
                except:
                    continue
                finally:
                    sock.close()
            sequence_number += 1
        throughput_end = time.time()
        throughput_time = throughput_end - throughput_begin
        time.sleep(1)
        self.get_statistics('UDP')
        throughput = (256 * 150 * .0001) / throughput_time
        print('Average Throughput: {}'.format(throughput))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--serverAddress', type=int, help='Specify the address of the udp client to connect to')
    parser.add_argument('-p', '--port', type=int, help='Specify the port of of the server that is listeneing for udp packets')
    udp_client = UDPClient('localhost', 10000)
    udp_client.run()

if __name__ == "__main__":
    main()
