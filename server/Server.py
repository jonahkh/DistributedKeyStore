import argparse
import logging
import os
import sys
import socket

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from server.RequestManager import RequestManager
from server.Receiver import ReceiverThread

logger = logging.getLogger(__name__)
BUFFER_SIZE = 256

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, help='Specify a port for the tcp server to listen')
    args = parser.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = socket.gethostbyname(socket.gethostname())
    sock.bind(server_address)
    sock.listen(1)
    print(sock.accept())
    # request_manager = RequestManager(args.port)
    # receiver = None
    # try:
    #     receiver = ReceiverThread(args.port, request_manager)
    #     receiver.start()
    #     request_manager.wait_completion()
    # except KeyboardInterrupt:
    #     print('terminating program')
    #     receiver.close_socket()
    #     os._exit(0)


if __name__ == "__main__":
    main()
