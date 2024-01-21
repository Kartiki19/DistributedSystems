from http.server import BaseHTTPRequestHandler, HTTPServer
from jsonrpclib import Server
import http.server
import socket
import time
import threading
import json
from urllib.parse import urlparse
from urllib.parse import parse_qs
HOST = 'localhost'
PORT = 8000 #default
data = {}
listener_track = {}
def utf8len(s):
    return len(s.encode('utf-8'))

class Listener(threading.Thread):
    def __init__(self, channel, thread_name):
        self.channel = channel
        self.broker = Server('http://localhost:1006')
        self.thread_name = thread_name
        self.message_queue = self.broker.subscribe(thread_name, channel)
        # self.
    def run(self,client):
        print(self.thread_name, "Run start, listen to messages ", self.channel)

        is_running = True
        counter = 0
        global data
        if self.thread_name not in data:
            data[self.thread_name] = []
        while is_running:
            message = self.broker.listen(self.thread_name, self.channel)
            if message != None:
                data[self.thread_name].append(message)
                time.sleep(0.1)
                is_running = (message['data'] != "End")
            else:
                time.sleep(0.2)

    def unsubscribe(self):
        self.broker.unsubscribe__(self.thread_name, self.channel)

class ThreadedServer(object):
    def __init__(self):
        print("Client started")

    def listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.bind((HOST, PORT))
            while True:
                sock.listen()
                conn, addr = sock.accept()
                t = threading.Thread(target=self.keepalive, args=(conn, addr))
                t.start()

    def keepalive(self, client, address):
        size = 1024
        with client:
            client.settimeout(5)
            while True:
                try:
                    global listener_track
                    request = client.recv(size).decode()
                    headers = request.split('\r\n')
                    REST  = headers[0].split()
                    print("print rest api", REST)
                    listener_1 = ''
                    if "/subscribe" in REST[1]: # == "/":
                        Params = REST[1].split('?')
                        listener_params = Params[1].split("=")
                        listener_name = listener_params[1].split('&')
                        listener_name = listener_name[0]
                        channel = listener_params[2]
                        listener_1 = Listener(channel, listener_name)
                        if(listener_name not in listener_track):
                            listener_track[listener_name] = {}
                        listener_track[listener_name][channel] = listener_1
                        listener_1.run(client)
                    elif "/getData" in REST[1]:
                        Params = REST[1].split('?')
                        listener_params = Params[1].split("=")
                        listener_name = listener_params[1]
                        self.getData(client,listener_name)
                    elif "/unsubscribe" in REST[1]:
                        Params = REST[1].split('?')
                        listener_params = Params[1].split("=")
                        listener_name = listener_params[1].split('&')
                        listener_name = listener_name[0]
                        channel = listener_params[2]
                        if(listener_name in listener_track):
                            if(channel in listener_track[listener_name]):
                                listener_track[listener_name][channel].unsubscribe()

                except Exception as e:
                    print(e)
                    break
        client.close()

    def getData(self,client,listener_name):
        global data
        print("this is data ", data)
        json_string = json.dumps(data[listener_name])
        client.sendall(str.encode("HTTP/1.1 200 OK\n",'iso-8859-1'))
        client.sendall(str.encode('Content-Type: application/json\n', 'iso-8859-1'))
        client.sendall(str.encode('Access-Control-Allow-Origin: *\n', 'iso-8859-1'))
        client.sendall(str.encode('\r\n'))
        client.sendall(json_string.encode())

def main():
    ThreadedServer().listen()

if __name__ == '__main__':  
    main()