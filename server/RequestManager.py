from queue import Queue
import logging
import os
import sys
import threading
import concurrent.futures
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from server.RequestThread import RequestThread
from server.PacketManager import PacketManager

THREAD_COUNT = 10
# have queue in request manager and have a thread inner class that waits on the queue
class RequestManager():
    def __init__(self, port):
        self.tasks = Queue(THREAD_COUNT)
        key_store = {}
        thread_lock = threading.Lock()
        self.threads = []
        packet_manager = PacketManager()
        server_addresses = (self.__get_server_addresses(), port)
        for _ in range(THREAD_COUNT):
            thread = RequestThread(self.tasks, key_store, thread_lock, packet_manager, server_addresses)
            self.threads.append(thread)
            thread.start()

    def add_job(self, connection, client_address):
        self.tasks.put({'connection': connection, 'client_address': client_address})

    def wait_completion(self):
        for thread in self.threads:
            thread.join()

    def kill_threads(self):
        for thread in self.threads:
            thread.kill_received = True

    def __get_server_addresses(self):
        return [
            '127.22.71.27',
            '127.22.71.28',
            '127.22.71.29'
            # '127.22.71.30',
            # '127.22.71.31'
        ]
