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
        self.request_manager = request_manager
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        server_address = socket.gethostbyname(socket.gethostname())
        server_address = (server_address, self.port)
        while True: # Wait until port opens.. if program terminated during execution socket might not have been closed
            try:
                self.sock.bind(server_address)
                break
            except:
                pass
        self.sock.listen(1)
        try:
            logger.error('Server {} listening on port {}'.format(server_address, self.port))
            while True:
                connection, client_address = self.sock.accept()
                self.request_manager.add_job(connection, client_address)
        except Exception as e:
            logger.error(e)    # Something really went wrong if this exception occurs
        finally:
            print('closing socket')
            if (not self.sock._closed):
                self.sock.close()

    def close_socket(self): # must be called to guarantee socket closes on main thread shutting down
        self.sock.close()   # socket may not be closed immediately if code crashes during a blocking call