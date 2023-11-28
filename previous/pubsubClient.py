from http.server import BaseHTTPRequestHandler, HTTPServer
from jsonrpclib import Server
import http.server
import socket
import time
import threading
import json
from urllib.parse import urlparse
from urllib.parse import parse_qs
HOST = "localhost"
PORT = 8000 #default
data = {}
listner_track = {}
def utf8len(s):
    return len(s.encode('utf-8'))

class Listener(threading.Thread):
    def __init__(self, chanel_name, thread_name):
        self.chanel_name = chanel_name
        self.broker = Server('http://localhost:1006')
        self.thread_name = thread_name
        self.message_queue = self.broker.subscribe(thread_name, chanel_name)
        # self.
    def run(self,client):
        print(self.thread_name, "Run start, listen to messages ", self.chanel_name)

        is_running = True
        counter = 0
        global data
        if self.thread_name not in data:
            data[self.thread_name] = []
        while is_running:
            message = self.broker.listen(self.thread_name, self.chanel_name)
            if message != None:
                data[self.thread_name].append(message)
                time.sleep(0.1)
                is_running = (message['data'] != "End")
            else:
                time.sleep(0.2)

    def unsubscribe(self):
        self.broker.unsubscribe__(self.thread_name, self.chanel_name)

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
                    global listner_track
                    request = client.recv(size).decode()
                    headers = request.split('\r\n')
                    REST  = headers[0].split()
                    print("print rest api", REST)
                    listener_1 = ''
                    if "/subscribe" in REST[1]: # == "/":
                        Params = REST[1].split('?')
                        listner_params = Params[1].split("=")
                        listner_name = listner_params[1].split('&')
                        listner_name = listner_name[0]
                        channel_name = listner_params[2]
                        listener_1 = Listener(channel_name, listner_name)
                        if(listner_name not in listner_track):
                            listner_track[listner_name] = {}
                        listner_track[listner_name][channel_name] = listener_1
                        listener_1.run(client)
                    elif "/getData" in REST[1]:
                        Params = REST[1].split('?')
                        listner_params = Params[1].split("=")
                        listner_name = listner_params[1]
                        self.getData(client,listner_name)
                    elif "/unsubscribe" in REST[1]:
                        Params = REST[1].split('?')
                        listner_params = Params[1].split("=")
                        listner_name = listner_params[1].split('&')
                        listner_name = listner_name[0]
                        channel_name = listner_params[2]
                        if(listner_name in listner_track):
                            if(channel_name in listner_track[listner_name]):
                                listner_track[listner_name][channel_name].unsubscribe()

                except Exception as e:
                    # print(e)
                    break
        client.close()

    def getData(self,client,listner_name):
        global data
        print("this is data ", data)
        json_string = json.dumps(data[listner_name])
        client.sendall(str.encode("HTTP/1.1 200 OK\n",'iso-8859-1'))
        client.sendall(str.encode('Content-Type: application/json\n', 'iso-8859-1'))
        client.sendall(str.encode('Access-Control-Allow-Origin: *\n', 'iso-8859-1'))
        client.sendall(str.encode('\r\n'))
        client.sendall(json_string.encode())

def main():
    ThreadedServer().listen()

if __name__ == '__main__':  
    main()