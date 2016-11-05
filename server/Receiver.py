import threading
import logging
import socket
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

class ReceiverThread(threading.Thread):
    def __init__(self, port, request_manager):
        threading.Thread.__init__(self)
        self.port = port
        self.server_address = socket.gethostbyname(socket.gethostname())
        self.request_manager = request_manager
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.server_address, self.port)
        self.sock.bind(server_address)

    def run(self):
        self.sock.listen(1)
        try:
            while True:
                connection, client_address = self.sock.accept()
                self.request_manager.add_job(connection, client_address)
        except Exception as e:
            print(e)
        finally:
            print('closing socket')
            if (not self.sock._closed):
                self.sock.close()

    def close_socket(self):
        self.sock.close()

