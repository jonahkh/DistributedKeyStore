import socket
import argparse
import logging
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from server.RequestThread import RequestThread
from xmlrpc.server import SimpleXMLRPCServer

logger = logging.getLogger(__name__)
BUFFER_SIZE = 256


class Server():
    def __init__(self, port, type, server_address):
        self.server_address = server_address
        self.port = port
        if (type == 'tcp'):
            self.__tcp_server()
        elif (type == 'rpc'):
            self.__rpc_server()
        elif (type == 'udp'):
            self.__udp_server()

    def rpc_request(self, data):
        thread = RequestThread(data, None, 'rpc', self.port)
        thread.start()
        try:
            thread.join()
            result = thread.get_result()
            return result
        except Exception as e:
            print(e)

    def __rpc_server(self):
        server = SimpleXMLRPCServer((self.server_address, self.port), allow_none=True, logRequests=False)
        server.register_function(self.rpc_request, "rpc_request")

        server.serve_forever()

    def __tcp_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.server_address, self.port)
        sock.bind(server_address)
        sock.listen(1)
        try:
            while True:
                connection, client_address = sock.accept()
                RequestThread(connection, client_address, 'tcp').start()
        except Exception as e:
            print(e)
        finally:
            print('closing socket')
            sock.close()

    def __udp_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = (self.server_address, self.port)
        sock.bind(server_address)
        try:
            while True:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                RequestThread(data, addr, 'udp', self.port).start()
        except Exception as e:
            print(e)
        finally:
            sock.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tcp', type=int, help='Specify a port for the tcp server to listen')
    parser.add_argument('-u', '--udp', type=int, help='Specify a port for the udp server to listen')
    parser.add_argument('-r', '--rpc', type=int, help='Specify a port for the tcp server to listen')
    args = parser.parse_args()
    server_address = socket.gethostbyname(socket.gethostname())

    if (args.tcp):
        Server(args.tcp, 'tcp', server_address)
    elif (args.udp):
        Server(args.udp, 'udp', server_address)
    elif (args.rpc):
        Server(args.rpc, 'rpc', server_address)
    else:
        logger.error('invalid arguments, at least one of -t, -u, -r are required. Run with -h for help')


if __name__ == "__main__":
    main()
