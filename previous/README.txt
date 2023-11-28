Author - Prerak Mathur & Hima Mallampati 
Application Name - Sports Broadcast Notification Application

There are three componenets in the application - Broker, Client (Subscriber), Server (Publisher).
Install all the dependencies.

1) Run the Broker - python .\pubsub.py
2) Run the Server - python .\pubsubServer.py
3) Run the client - python .\pubsubClient.py

Open the index.html page in any browser locally (static page do not need to serve it from any server)

Open postman (or any API testing platform)

	1) Create a POST request to http://localhost:5500
	2) In the body of the request (form-data) send these fields
		a) sender (any string value)
		b) channel_name (basketball or soccer)
		c) num_msg (any integer value)
		d) id (any integer value)
		e) msg_type (info or end)
	3) Fire the request

On the webpage (index.html) Subscribe to soccer and/or basketball (based on the POST request) and see the notificaitons coming through.