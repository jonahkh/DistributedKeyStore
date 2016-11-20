import threading
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from server.PacketManager import PacketManager

class KeyStore():
    def __init__(self):
        self.thread_lock = threading.Lock()
        self.packet_manager = PacketManager()
        self.key_store = {}

    def delete(self, key):
        status = 'failure'
        response = None
        self.thread_lock.acquire()
        if key in self.key_store:
            self.key_store.pop(key)
            status = 'success'
        else:
            response = 'Key not found'
        self.thread_lock.release()
        return self.packet_manager.get_packet('tcp', status, response, 'DELETE')

    def get(self, key):
        status = 'failure'
        self.thread_lock.acquire()
        if key in self.key_store:
            response = self.key_store.get(key)
            status = 'success'
        else:
            response = 'Key not found'
        self.thread_lock.release()
        return self.packet_manager.get_packet('tcp', status, response, 'GET')

    def put(self, key, value):
        self.thread_lock.acquire()
        self.key_store[key] = value
        self.thread_lock.release()
        print(self.key_store)
        return self.packet_manager.get_packet('tcp', 'success', None, 'PUT')