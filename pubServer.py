from http.server import BaseHTTPRequestHandler, HTTPServer
from jsonrpclib import Server
import time
import threading
import cgi
import random
import requests

API_KEY = "7c78d5daa857cd521d7506ef34968c30"

class Sender(threading.Thread):

    

    def __init__(self, thread_name, channel, full_thread_name, nb_of_message_2_send, message_type, game_id):
        print("Server has started!")
        threading.Thread.__init__(self, name=full_thread_name)
        self.thread_name = thread_name
        self.channel = channel
        self.full_thread_name = full_thread_name
        self.broker = Server('http://localhost:1006')
        self.nb_of_message_2_send = nb_of_message_2_send
        self.message_type = message_type
        self.game_id = game_id

        

    def run(self):
        print(self.full_thread_name, "Run start, send ",
              self.nb_of_message_2_send,
              "with a pause of 50ms between each one...")
        if(self.message_type == "end"):
            self.broker.publish(self.channel, "End")
            return
        for counter in range(self.nb_of_message_2_send):
            message = self.getData(counter)
            print("message is this", message)
            self.broker.publish(self.channel, message)
            time.sleep(0.05)

        print(self.full_thread_name, self.nb_of_message_2_send,
              "sent End to stop channels listeners.")
    
    def getData(self, counter): 
        city = self.channel     
        apiUrl = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}"       
        json_data = requests.get(apiUrl).json()
        condition = json_data['weather'][0]['main']
        temp = int(json_data['main']['temp'] - 273.15)
        min_temp = int(json_data['main']['temp_min'] - 273.15)
        max_temp = int(json_data['main']['temp_max'] - 273.15)
        pressure = json_data['main']['pressure']
        humidity = json_data['main']['humidity']
        wind = json_data['wind']['speed']

        final_info = condition + "\n" + str(temp) + "°C" 
        final_data = '{"City":"' + str(city) + '",'
        final_data += '"Min_Temp":"' + str(min_temp) + '",'
        final_data += '"Max_Temp":"' + str(max_temp) + '",'
        final_data += '"Pressure":"' + str(pressure) + '",'
        final_data += '"Humidity":"' + str(humidity) + '",'
        final_data += '"Wind_Speed":"' + str(wind) + '"}'
        return final_data   

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        message = "Hello, World!"
        self.wfile.write(bytes(message, "utf8"))
    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )
        thread_name = form.getvalue("sender")
        channel = form.getvalue("channel")
        number_of_message_on_channel_1 = int(form.getvalue("num_msg"))
        message_type = (form.getvalue("msg_type"))
        game_id = int(form.getvalue("id"))
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        full_thread_name = "Sender : " + thread_name + " on " + channel
        worker = Sender(thread_name, channel, full_thread_name, number_of_message_on_channel_1, message_type, game_id)
        worker.start()

with HTTPServer(('', 5500), handler) as server:

    server.serve_forever()


    
