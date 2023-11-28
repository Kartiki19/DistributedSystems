from http.server import BaseHTTPRequestHandler, HTTPServer
from jsonrpclib import Server
import time
import threading
import cgi
import random


class WeatherSender(threading.Thread):

    def __init__(self, thread_name, channel_name, full_thread_name, num_of_updates, location_id):
        print("Weather Server has started!")
        threading.Thread.__init__(self, name=full_thread_name)
        self.thread_name = thread_name
        self.channel_name = channel_name
        self.full_thread_name = full_thread_name
        self.broker = Server('http://localhost:1006')
        self.num_of_updates = num_of_updates
        self.location_id = location_id

    def run(self):
        print(self.full_thread_name, "Run start, sending ",
              self.num_of_updates,
              "with a pause of 50ms between each one...")

        for counter in range(self.num_of_updates):
            weather_data = self.get_weather_data(counter)
            print("Weather update:", weather_data)
            self.broker.publish(self.channel_name, weather_data)
            time.sleep(0.05)

        print(self.full_thread_name, self.num_of_updates,
              "sent End to stop channel listeners.")

    def get_weather_data(self, counter):
        data = '{"location_id":"' + str(self.location_id) + '",'
        data += '"temperature":"' + str(random.uniform(20.0, 30.0)) + '",'
        data += '"humidity":"' + str(random.uniform(50.0, 80.0)) + '",'
        data += '"wind_speed":"' + str(random.uniform(5.0, 15.0)) + '"}'
        return data


class WeatherHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        message = "Welcome to Weather Updates Server!"
        self.wfile.write(bytes(message, "utf8"))

    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )

        if "num_updates" not in form:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(bytes("Bad Request: 'num_updates' field is required.", "utf8"))
            return

        thread_name = form.getvalue("sender")
        channel_name = form.getvalue("channel_name")
        num_of_updates = int(form.getvalue("num_updates"))
        location_id = int(form.getvalue("location_id"))

        self.send_response(200)
        self.end_headers()
        full_thread_name = "WeatherSender: " + thread_name + " on " + channel_name
        weather_worker = WeatherSender(thread_name, channel_name, full_thread_name, num_of_updates, location_id)
        weather_worker.start()


with HTTPServer(('', 5505), WeatherHandler) as server:
    server.serve_forever()
