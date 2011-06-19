# -*- coding: utf-8 -*-

import socket
from xml.dom import minidom

import socket, hashlib, thread, time, random, pywapi, urllib

class TlenClient:
	def __init__(self, host, port, user, password):
		self.host = host
		self.port = port
		self.user = user
		self.password = password

	def _initSession(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((self.host, self.port))

		connectionString = """<s v="9" t="06000224">"""

		self.sock.send(connectionString)
		result = self.sock.recv(1024)

		if result == '<stream:error>blad</stream:error></stream:stream>':
			raise Exception, 'Unexpected error'
		else:
			result = '<?xml version="1.0" encoding="utf-8"?>%s</s>' % result
			DOMTree = minidom.parseString(result)
			self.sessionId = DOMTree.childNodes[0].getAttribute("i")

	def _passcode(self):
		magic1 = 0x50305735
		magic2 = 0x12345671
		sum = 7
		for i in self.password:
			z = ord(i);
			if z == 32:
				continue
			if z == 9:
				continue

			magic1 = magic1 ^ ((((magic1 & 0x3f) + sum) * z) + (magic1 << 8))
			magic2 = magic2 + ((magic2 << 8) ^ magic1);
			sum += z;
			magic1 = magic1 & 0x7fffffff;
			magic2 = magic2 & 0x7fffffff;
		
		return '%08x%08x' % (magic1, magic2)
	
	def connect(self):
		self._initSession()
		self._auth()

	def _auth(self):
		authString = """
		<iq type="set" id="%s">
		    <query xmlns="jabber:iq:auth">
			<username>%s</username>
			<digest>%s</digest>
			<resource>t</resource>
			<host>tlen.pl</host>
		    </query>
		</iq>
		""" % (self.sessionId, self.user, hashlib.sha1(str(self.sessionId)+self._passcode()).hexdigest())

		self.sock.send(authString)
		result = self.sock.recv(1024)

		result = '<?xml version="1.0" encoding="utf-8"?><tlenobot>%s</tlenobot>' % result

		DOMTree = minidom.parseString(result)
		type = DOMTree.childNodes[0].childNodes[0].getAttribute("type")

		if type == 'error':
			raise Exception, 'Bad login and/or password'

	def setPresence(self, presence, status):
		msg = """
		<presence>
			<show>%s</show>
			<status>%s</status>
		</presence>
		""" % (presence, status)

		self.sock.send(msg)
		return self.sock.recv(1024)

	def sendMessage(self, user, message):
		msg = """
		<message to="%s">
		    <body>%s</body>
		</message>
		""" % (user, message)

		return self.sock.send(msg)

	def makeSubscription(user):
		msg = """
		<presence to="%s" type="subscribe"/>
		""" % (user,)

	def answerSubscription(user):
		msg = """
		<presence to="%s" type="subscribed"/>
		""" % (user,)

	def ping(self,delay):
	    while 1:
		time.sleep(delay)
		self.sock.send("  \t  ")

	def listen(self, callback):
		while 1:
			time.sleep(1)

			try:
				response = self.sock.recv(1024)
				if response:
					response = '<tlenobot>%s</tlenobot>' % self.sock.recv(1024)
					callback(response)
				
			except:
				pass

tlenobotClient = TlenClient(host = 's1.tlen.pl', port = 443, user = 'tlenobot', password = 'tlenobot')
tlenobotClient.connect()
tlenobotClient.setPresence('chat', 'Wejdz i zobacz')

def moja_funkcja(response):
	resp = minidom.parseString(response)

	message =  resp.getElementsByTagName('message')
	if len(message) > 0:
		userFrom = message[0].getAttribute('from')

		messageBody = urllib.unquote(message[0].childNodes[0].childNodes[0].nodeValue)
		tlenobotClient.sendMessage(userFrom, messageBody[::-1])

thread.start_new_thread(tlenobotClient.listen, (moja_funkcja,))
print 'Starting...'
time.sleep(5)
print 'Started :)'

while 1:
	tlenobotClient.ping(15)
