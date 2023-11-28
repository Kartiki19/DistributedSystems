import warnings
from multiprocessing.pool import ThreadPool
from threading import Lock
from threading import Thread
from queue import Queue, PriorityQueue, Empty
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
pool = ThreadPool(processes=1)
class PubSubBase():
    def __init__(self, max_queue_in_a_channel=100, max_id_4_a_channel=2**31):
        self.max_queue_in_a_channel = max_queue_in_a_channel
        self.max_id_4_a_channel = max_id_4_a_channel

        self.channels = {}
        self.count = {}

        self.channels_lock = Lock()
        self.count_lock = Lock()

    def subscribe_(self, listner, channel, is_priority_queue):

        if not channel:
            raise ValueError('channel : None value not allowed')

        if channel not in self.channels:
            self.channels_lock.acquire()
            if channel not in self.channels:
                self.channels[channel] = {}
            self.channels_lock.release()

        message_queue = None
        if is_priority_queue:
            message_queue = ChanelPriorityQueue(self, channel)
        else:
            message_queue = ChanelQueue(self, channel)
        self.channels[channel][listner] = message_queue

        return message_queue

    def unsubscribe(self, listner, channel, message_queue):
        if not channel:
            raise ValueError('channel : None value not allowed')
        if not message_queue:
            raise ValueError('message_queue : None value not allowed')
        if channel in self.channels:
            self.channels[channel][listner].remove(message_queue)

    def publish_(self, channel, message, is_priority_queue, priority):

        if priority < 0:
            raise ValueError('priority must be > 0')
        if not channel:
            raise ValueError('channel : None value not allowed')
        if not message:
            raise ValueError('message : None value not allowed')

        if channel not in self.channels:
            self.channels_lock.acquire()
            if channel not in self.channels:
                self.channels[channel] = {}
            self.channels_lock.release()

        self.count_lock.acquire()
        if channel not in self.count:
            self.count[channel] = 0
        else:
            self.count[channel] = ((self.count[channel] + 1) %
                                   self.max_id_4_a_channel)
        self.count_lock.release()

        _id = self.count[channel]

        for listn in self.channels[channel]:
            channel_queue = self.channels[channel][listn]
            if channel_queue.qsize() >= self.max_queue_in_a_channel:
                warnings.warn((
                    f"Queue overflow for channel {channel}, "
                    f"> {self.max_queue_in_a_channel} "
                    "(self.max_queue_in_a_channel parameter)"))
            else:  # No overflow on this channel_queue
                if is_priority_queue:
                    channel_queue.put((priority,
                                       OrderedDict(data=message, id=_id)),
                                      block=False)
                else:
                    channel_queue.put({'channel': channel, 'data': message, 'id': _id},
                                      block=False)

    def getMessageQueue_(self, listner, channel_name):
        if self.channels[channel_name][listner].empty():
            return None
        return self.channels[channel_name][listner]

class ChanelQueue(Queue):
    def __init__(self, parent, channel):
        super().__init__()
        self.parent = parent
        self.name = channel

    def listen(self, block=True, timeout=None):
        while True:
            try:
                data = self.get(block=block, timeout=timeout)
                assert isinstance(data, dict) and len(data) == 3,\
                       "Bad data in chanel queue !"
                yield data
            except Empty:
                return

    def unsubscribe(listner, channel_name, self):
        self.parent.unsubscribe(listner, channel_name, self)


class ChanelPriorityQueue(PriorityQueue):

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
                       len(priority_data[1]) == 2, "Bad data in chanel queue !"
                yield priority_data[1]
            except Empty:
                return

    def unsubscribe(self):
        self.parent.unsubscribe(self.name, self)


class PubSub(PubSubBase):
    def subscribe(self, listner, channel):
        return self.subscribe_(listner, channel, False)

    def publish(self, channel, message):
        self.publish_(channel, message, False, priority=100)

    def getMessageQueue(self, listner, channel_name):
        return self.getMessageQueue_(listner, channel_name)

class PubSubPriority(PubSubBase):
    def subscribe(self, channel):
        return self.subscribe_(channel, True)

    def publish(self, channel, message, priority=100):
        self.publish_(channel, message, True, priority)


class OrderedDict(dict):
    def __lt__(self, other):
        return self['id'] < other['id']

communicator = PubSub()

def publishThreaded(channel_name, message):
    global communicator
    communicator.publish(channel_name, message)
    print("channel name" , channel_name, "message is ", message)

def subscribeThreaded(listner, channel_name):
    global communicator
    print("this is subscribe", listner, channel_name)
    communicator.subscribe(listner, channel_name)
    return listner

def listenThreaded(listner, channel_name):
    global communicator
    message_queue = communicator.getMessageQueue(listner, channel_name)
    if message_queue == None:
        return None
    message = next(message_queue.listen())
    return message

def listen(listner, chanel_name):
    global pool
    thread = pool.apply_async(listenThreaded, (listner,chanel_name))
    message = thread.get()
    return message

def subscribe(listner, chanel_name):
    thread = Thread(target = subscribeThreaded, args = (listner, chanel_name))
    thread.start()
    thread.join()

def publish(channel_name, message):
    thread = Thread(target = publishThreaded, args = (channel_name, message))
    thread.start()
    thread.join()

def unsubscribeThreaded(listner,channel_name):
    global communicator
    message_queue = communicator.getMessageQueue(listner, channel_name)
    message_queue.unsubscribe(listner,channel_name)

def unsubscribe__(listner, chanel_name):
    print("unsub suc")
    thread = Thread(target = unsubscribeThreaded, args = (listner, channel_name))
    thread.start()
    thread.join()

def main():
    server = SimpleJSONRPCServer(('localhost', 1006))
    server.register_function(publish)
    server.register_function(subscribe)
    server.register_function(listen)
    server.register_function(unsubscribe__)
    print("Broker started")
    server.serve_forever()

if __name__ == '__main__':
    main()