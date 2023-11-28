import warnings
from multiprocessing.pool import ThreadPool
from threading import Lock, Thread
from queue import Queue, Empty, PriorityQueue
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
from collections import OrderedDict

class WeatherPubSubBase():
    def __init__(self, max_queue_in_a_channel=100, max_id_4_a_channel=2**31):
        self.max_queue_in_a_channel = max_queue_in_a_channel
        self.max_id_4_a_channel = max_id_4_a_channel

        self.channels = {}
        self.count = {}

        self.channels_lock = Lock()
        self.count_lock = Lock()

    def subscribe_(self, listener, channel, is_priority_queue):
        if not channel:
            raise ValueError('channel: None value not allowed')

        if channel not in self.channels:
            with self.channels_lock:
                if channel not in self.channels:
                    self.channels[channel] = {}

        message_queue = None
        if is_priority_queue:
            message_queue = WeatherChannelPriorityQueue(self, channel)
        else:
            message_queue = WeatherChannelQueue(self, channel)

        with self.channels_lock:
            self.channels[channel][listener] = message_queue

        return message_queue

    def unsubscribe(self, listener, channel, message_queue):
        if not channel:
            raise ValueError('channel: None value not allowed')
        if not message_queue:
            raise ValueError('message_queue: None value not allowed')

        with self.channels_lock:
            if channel in self.channels:
                self.channels[channel][listener].remove(message_queue)

    def publish_(self, channel, message, is_priority_queue, priority):
        if priority < 0:
            raise ValueError('priority must be >= 0')
        if not channel:
            raise ValueError('channel: None value not allowed')
        if not message:
            raise ValueError('message: None value not allowed')

        with self.channels_lock:
            if channel not in self.channels:
                self.channels[channel] = {}

        with self.count_lock:
            if channel not in self.count:
                self.count[channel] = 0
            else:
                self.count[channel] = ((self.count[channel] + 1) %
                                       self.max_id_4_a_channel)

        _id = self.count[channel]

        for listener in self.channels[channel]:
            channel_queue = self.channels[channel][listener]
            if channel_queue.qsize() >= self.max_queue_in_a_channel:
                warnings.warn((
                    f"Queue overflow for channel {channel}, "
                    f">{self.max_queue_in_a_channel} "
                    "(self.max_queue_in_a_channel parameter)"))
            else:
                if is_priority_queue:
                    channel_queue.put((priority,
                                       OrderedDict(data=message, id=_id)),
                                      block=False)
                else:
                    channel_queue.put({'channel': channel, 'data': message, 'id': _id},
                                      block=False)

    def get_message_queue_(self, listener, channel_name):
        if self.channels[channel_name][listener].empty():
            return None
        return self.channels[channel_name][listener]

class WeatherChannelQueue(Queue):
    def __init__(self, parent, channel):
        super().__init__()
        self.parent = parent
        self.name = channel

    def listen(self, block=True, timeout=None):
        while True:
            try:
                data = self.get(block=block, timeout=timeout)
                assert isinstance(data, dict) and len(data) == 3,\
                       "Bad data in channel queue!"
                yield data
            except Empty:
                return

    def unsubscribe(self, listener, channel_name):
        self.parent.unsubscribe(listener, channel_name, self)

class WeatherChannelPriorityQueue(PriorityQueue):
    def __init__(self, parent, channel):
        super().__init__()
        self.parent = parent
        self.name = channel

    def listen(self, block=True, timeout=None):
        while True:
            try:
                priority_data = self.get(block=block, timeout=timeout)
                assert isinstance(priority_data, tuple) and \
                       len(priority_data) == 2 and \
                       isinstance(priority_data[1], dict) and \
                       len(priority_data[1]) == 2, "Bad data in channel queue!"
                yield priority_data[1]
            except Empty:
                return

    def unsubscribe(self):
        self.parent.unsubscribe(self.name, self)

class WeatherPubSub(WeatherPubSubBase):
    def subscribe(self, listener, channel):
        return self.subscribe_(listener, channel, False)

    def publish(self, channel, message):
        self.publish_(channel, message, False, priority=100)

    def get_message_queue(self, listener, channel_name):
        return self.get_message_queue_(listener, channel_name)

class WeatherPubSubPriority(WeatherPubSubBase):
    def subscribe(self, channel):
        return self.subscribe_(channel, True)

    def publish(self, channel, message, priority=100):
        self.publish_(channel, message, True, priority)

communicator = WeatherPubSub()

def publish(channel_name, message):
    global communicator
    communicator.publish(channel_name, message)
    print("channel name", channel_name, "message is", message)

def subscribe(listener, channel_name):
    global communicator
    print("this is subscribe", listener, channel_name)
    communicator.subscribe(listener, channel_name)
    return listener

def listen(listener, channel_name):
    global pool
    thread = pool.apply_async(listen_threaded, (listener, channel_name))
    message = thread.get()
    return message

def unsubscribe(listener, channel_name):
    print("unsub success")
    thread = Thread(target=unsubscribe_threaded, args=(listener, channel_name))
    thread.start()
    thread.join()

def main():
    server = SimpleJSONRPCServer(('localhost', 1006))
    server.register_function(publish)
    server.register_function(subscribe)
    server.register_function(listen)
    server.register_function(unsubscribe)
    print("Broker started")
    server.serve_forever()

if __name__ == '__main__':
    main()