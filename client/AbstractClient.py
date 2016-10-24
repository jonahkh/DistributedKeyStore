import time
import statistics
class AbstractClient(object):
    def __init__(self):
        self.timing_information = {'PUT': [], 'GET': [], 'DELETE': []}

    def get_timing_information(self):
        return self.timing_information


    def get_time_stamp(self):
        return 'at local time: {}, system time: {}'.format(time.asctime(), time.time())

    def get_statistics(self, type):
        print('\n\nFinal Results for {} (in milliseconds):\n'.format(type))
        for operation in self.timing_information:
            print(operation + ':')
            print('\t Average: {}'.format(statistics.mean(self.timing_information[operation])))
            print('\tVariance: {}'.format(statistics.stdev(self.timing_information[operation])))
