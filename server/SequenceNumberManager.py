import threading

class SequenceNumberManager():
    def __init__(self):
        self.sequence_number = 0
        self.thread_lock = threading.Lock()
        self.highest_proposal_number = 0
        self.highest_proposed_value = None

    def increment(self):
        self.thread_lock.acquire()
        self.sequence_number += 1
        self.thread_lock.release()
        return self.sequence_number

    def get_sequence_number(self):
        return self.sequence_number

    def set(self, value):
        self.thread_lock.acquire()
        self.sequence_number = value
        self.thread_lock.release()
        return value

    def set_highest_value(self, key=None, value=None):
        self.thread_lock.acquire()
        self.highest_proposed_value = Value(key, value) if key else None
        self.thread_lock.release()

    def set_highest_proposed_number(self, value):
        self.thread_lock.acquire()
        self.highest_proposal_number = value
        self.thread_lock.release()

class Value():
    def __init__(self, key, value=None):
        self.__key = key
        self.__value = value