import threading
# key_store = {}
# class KeyStore:
#     def __init__(self):
# #         thread.start_new_thread(function, args)
#         self.thread_lock = threading.Lock()
#         
#     def put(self, key, value):
#         thread = self.put_thread(self.thread_lock, key, value)
#         thread.start()
#         thread.join()
#     
#     def get(self, key):
#         thread = self.get_thread(self.thread_lock, key)
#         thread.start()
#         thread.join()
#         return thread.value
#         
#         
#     class put_thread(threading.Thread):
#         def __init__(self, thread_lock, key, value):
#             self.key = key
#             self.value = value
#             self.thread_lock = thread_lock
#             threading.Thread.__init__(self)
#             
#         def run(self):
#             self.thread_lock.acquire()
#             key_store[self.key] = self.value
#             print(key_store)
#             self.thread_lock.release()
#     
#     class get_thread(threading.Thread):
#         def __init__(self, thread_lock, key):
#             self.key = key
#             self.thread_lock = thread_lock
#             self.value = None
#             threading.Thread.__init__(self)
#         
#         def run(self):
#             self.thread_lock.acquire()
#             self.value = key_store[self.key]
#             return self.value

# class KeyStore:
#     def request(self, operation, key, value=None):
#         thread = self.thread(operation, key, value)
#         thread.start()
#         print(key_store)
#         if (operation == 'GET'):
#             return thread.value
#         
#         
#     class thread(threading.Thread):
#         def __init__(self, operation, key, value=None):
#             threading.Thread.__init__(self)
#             self.operation = operation
#             self.key = key
#             self.value = value
#         
#         def run(self):
#             if (self.operation == "DELETE"):
#                 self.delete()
#             elif (self.operation == "GET"):
#                 self.get()
#             elif (self.operation == "PUT"):
#                 self.put()
#         
#         def delete(self):
#             thread_lock.acquire()
#             key_store.pop(self.key)
#             thread_lock.release()
#             
#         def get(self):
#             print('in get keystore')
#             thread_lock.acquire()
#             self.value = key_store.get(self.key)
#             thread_lock.release()
#             
#         def put(self):
#             thread_lock.acquire()
#             key_store[self.key] = self.value
#             thread_lock.release()
# 
# class KeyStore(threading.Thread):
#     def request(self, operation, key, value=None):
#         thread = self.thread(operation, key, value)
#         thread.start()
#         print(key_store)
#         if (operation == 'GET'):
#             return thread.value
#         
#         
#     class thread(threading.Thread):
#         pass
key_store = {}
thread_lock = threading.Lock()

class thread(threading.Thread):
    def __init__(self, connection, protocol):
        threading.Thread.__init__(self)
        self.connection = connection
        self.protocol = protocol
        print('received data')

#         self.message = message
#         self.operation = message.get('operation')
#         self.value = message.get('value')
#         self.key = message.get('key')
        
        
#             def __init__(self, operation, key, value=None):
#             threading.Thread.__init__(self)
#             self.operation = operation
#             self.key = key
#             self.value = value
    def get_data(self):
        data = ''
        while True:
            msg = self.connection.recv(BUFFER_SIZE).decode()
            if msg:
                data += msg
                self.connection.sendall('{"status": "success"}'.encode())
                print('data: ' + data)
                print('msg: ' + msg)
            else:
                break
        
#         connection.close()
        print('loading data')
        data = json.loads(data)
        print('data loaded')
        if (data.get('operation') != 'GET' and self.protocol == 'tcp'):
            self.connection.close()
        print('final data: ' + str(data))
        return data
                
                
    def run(self):
        print('in run')
        data = self.get_data()
        print(data)
        key = data.get('key')
        value = data.get('value')
        operation = data.get('operation')
        print('data = ' + str(data))
        response = None
        if (operation == "DELETE"):
            response = self.delete(key)
        elif (operation == "GET"):
            response = self.get(key)
        elif (operation == "PUT"):
            response = self.put(key, value)
        if (data.get('operation') == "GET"):
            print('GET request: {}'.format(response))
            message = {'status': 'success', 'value': response}
            self.connection.sendall(json.dumps(message).encode())
            self.connection.close()
        print('keystore: ' + str(key_store))
        print('closing connection\n\n')

        
    def delete(self, key):
        thread_lock.acquire()
        key_store.pop(key)
        thread_lock.release()
        
    def get(self, key):
        print('in get keystore')
        thread_lock.acquire()
        value = key_store.get(key)
        thread_lock.release()
        return value
        
    def put(self, key, value):
        thread_lock.acquire()
        print('lock acquired')
        key_store[key] = value
        thread_lock.release()
        print('lock released')
                
                
            
        