from http.server import BaseHTTPRequestHandler, HTTPServer
from jsonrpclib import Server
import http.server
import socket
import time
import threading
import json
from urllib.parse import urlparse, parse_qs

HOST = "localhost"
PORT = 8000  # default
data = {}
listener_track = {}


class WeatherListener(threading.Thread):
    def __init__(self, channel_name, listener_name):
        self.channel_name = channel_name
        self.broker = Server('http://localhost:1006')
        self.listener_name = listener_name
        self.message_queue = self.broker.subscribe(listener_name, channel_name)

    def run(self):
        print(self.listener_name, "Run start, listen to messages ", self.channel_name)

        is_running = True
        global data
        if self.listener_name not in data:
            data[self.listener_name] = []
        while is_running:
            message = self.broker.listen(self.listener_name, self.channel_name)
            if message is not None:
                data[self.listener_name].append(message)
                time.sleep(0.1)
                is_running = (message['data'] != "End")
            else:
                time.sleep(0.2)

        print(self.listener_name, "Stopped listening.")
        self.unsubscribe()

    def unsubscribe(self):
        self.broker.unsubscribe__(self.listener_name, self.channel_name)


class ThreadedWeatherServer(object):
    def __init__(self):
        print("Weather Server started")

    def listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.bind((HOST, PORT))
            while True:
                sock.listen()
                conn, addr = sock.accept()
                t = threading.Thread(target=self.handle_connection, args=(conn, addr))
                t.start()

    def handle_connection(self, client, address):
        size = 1024
        with client:
            client.settimeout(5)
            while True:
                try:
                    global listener_track
                    request = client.recv(size).decode()
                    headers = request.split('\r\n')
                    REST = headers[0].split()
                    print("print REST API", REST)
                    listener_1 = ''
                    if "/subscribe" in REST[1]:  # == "/":
                        Params = REST[1].split('?')
                        listener_params = Params[1].split("=")
                        listener_name = listener_params[1].split('&')
                        listener_name = listener_name[0]
                        channel_name = listener_params[2]
                        listener_1 = WeatherListener(channel_name, listener_name)
                        if listener_name not in listener_track:
                            listener_track[listener_name] = {}
                        listener_track[listener_name][channel_name] = listener_1
                        listener_1.run(client)
                    elif "/getData" in REST[1]:
                        Params = REST[1].split('?')
                        listener_params = Params[1].split("=")
                        listener_name = listener_params[1]
                        self.get_data(client, listener_name)
                    elif "/unsubscribe" in REST[1]:
                        Params = REST[1].split('?')
                        listener_params = Params[1].split("=")
                        listener_name = listener_params[1].split('&')
                        listener_name = listener_name[0]
                        channel_name = listener_params[2]
                        if listener_name in listener_track:
                            if channel_name in listener_track[listener_name]:
                                listener_track[listener_name][channel_name].unsubscribe()

                except Exception as e:
                    # print(e)
                    break
        client.close()

    def get_data(self, client, listener_name):
        global data
        print("this is data ", data)
        json_string = json.dumps(data[listener_name])
        client.sendall(str.encode("HTTP/1.1 200 OK\n", 'iso-8859-1'))
        client.sendall(str.encode('Content-Type: application/json\n', 'iso-8859-1'))
        client.sendall(str.encode('Access-Control-Allow-Origin: *\n', 'iso-8859-1'))
        client.sendall(str.encode('\r\n'))
        client.sendall(json_string.encode())


def main():
    ThreadedWeatherServer().listen()


if __name__ == '__main__':
    main()
