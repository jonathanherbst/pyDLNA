'''
Created on Aug 4, 2013

@author: Jonathan
'''

import time
from collections import OrderedDict

ADDRESS = ("239.255.255.250", 1900)

def initialize(userAgent):
	global USER_AGENT
	USER_AGENT = userAgent

def getUserAgent():
	global USER_AGENT
	if "USER_AGENT" not in globals():
		USER_AGENT = "not/1.0 UPnP/1.1 initialized/2.7"
	return USER_AGENT

class Device(object):
	
	MAX_BOOT_ID = 2**31 - 1
	MAX_CONFIG_ID = 2**24 - 1
	
	def __init__(self, uuid, urn, location=None, configId=0, bootId=int(time.time())):
		if not (0 <= int(bootId) <= self.MAX_BOOT_ID): raise ValueError("bootId must be between zero and %d" % self.MAX_BOOT_ID)
		if not (0 <= int(configId) <= self.MAX_CONFIG_ID): raise ValueError("configId must be between zero and %d" % self.MAX_CONFIG_ID)
		
		self._uuid = uuid
		self._urn = urn
		self._configId = int(configId)
		self._bootId = int(bootId)
		self._devices = [] 
		self._services = []
		self._location = location
		
	@property
	def uuid(self):
		return self._uuid
	
	@property
	def urn(self):
		return self._urn
	
	@property
	def configId(self):
		return self._configId
	
	@property
	def bootId(self):
		return self._bootId
	
	@property
	def devices(self):
		return self._devices
	
	@property
	def services(self):
		return self._services
	
	@property
	def location(self):
		return self._location
	
	def updateBootId(self):
		self._bootId = (self._bootId + 1) % (self.MAX_BOOT_ID + 1)
		
	def addDevice(self, device):
		self._devices.append(device)
		
	def addService(self, service):
		self._services.append(service)
	
class Service(object):
	
	def __init__(self, urn):
		self._urn = urn
		
	@property
	def urn(self):
		return self._urn

def formatDate(t):
	return time.strftime("%a, %d %b %Y %H:%M:%S UTC", t)

def renderMessage(method, headers):
	HEADER_FORMAT = "%s: %s"
	return method + "\r\n" + "\r\n".join([HEADER_FORMAT % header for header in headers.items()]) + "\r\n"

def parseMessage(message):
	lines = message.split("\r\n")
	headers = {}
	for line in lines[1:]:
		components = line.split(":", 1)
		if len(components) == 1:
			headers[components[0].strip()] = ""
		elif len(components) == 2:
			headers[components[0].strip()] = components[1].strip()
	return lines[0], headers

NOTIFY_METHOD = "NOTIFY * HTTP/1.1"
SEARCH_METHOD = "M-SEARCH * HTTP/1.1"
RESPONSE_METHOD = "HTTP/1.1 200 OK"

ALIVE_HEADERS = {"HOST": "%s:%d" % ADDRESS,
				"CACHE-CONTROL": "",
				"LOCATION": "",
				"NT": "",
				"NTS": "ssdp:alive",
				"SERVER": "",
				"USN": "", 
				"BOOTID.UPNP.ORG": "",
				"CONFIGID.UPNP.ORG": ""}

def renderAliveMessages(device, maxAge, root=True, headers=ALIVE_HEADERS):
	messages = []
	if root:
		headers["CACHE-CONTROL"] = "max-age - %d" % maxAge
		headers["LOCATION"] = device.location
		headers["SERVER"] = getUserAgent()
		headers["BOOTID.UPNP.ORG"] = device.bootId
		headers["CONFIGID.UPNP.ORG"] = device.configId
		
		headers["NT"] = "upnp:rootdevice"
		headers["USN"] = "uuid:%s::upnp:rootdevice" % device.uuid
		messages.append(renderMessage(NOTIFY_METHOD, headers))
		
	headers["NT"] = "uuid:%s" % device.uuid
	headers["USN"] = "uuid:%s" % device.uuid
	messages.append(renderMessage(NOTIFY_METHOD, headers))
		
	headers["NT"] = "urn:%s" % device.urn
	headers["USN"] = "uuid:%s::urn:%s" % (device.uuid, device.urn)
	messages.append(renderMessage(NOTIFY_METHOD, headers))
		
	for child in device.devices:
		messages.extend(renderAliveMessages(child, maxAge, False, headers))
		
	for service in device.services:
		headers["NT"] = "urn:%s" % service.urn
		headers["USN"] = "uuid:%s::urn:%s" % (device.uuid, service.urn)
		messages.append(renderMessage(NOTIFY_METHOD, headers))
		
	return messages

def renderDeadMessages(device, maxAge):
	pass

def renderUpdateMessages(device, maxAge):
	pass

def renderSearchResponseMessages(device, maxAge, searchTarget, t=time.gmtime()):
	pass

def renderSearchMessage(maxAge, searchTarget):
	pass

def _renderHeaders(headers):
	HEADER_FORMAT = "%s: %s"
	return "\r\n".join([HEADER_FORMAT % header for header in headers.items()])

class _Message(object):
	
	def __init__(self, method, headers):
		self._method = method
		self._headers = headers
	
	def render(self):
		return self._method + "\r\n" + _renderHeaders(self._headers) + "\r\n"

class _NotifyMessage(_Message):
	def __init__(self, headers):
		_Message.__init__(self, "NOTIFY * HTTP/1.1", headers)

class SearchMessage(_Message):
	def __init__(self, mx, st):
		_Message.__init__(self, "M-SEARCH * HTTP/1.1",
						  OrderedDict([("HOST", "%s:%d" % ADDRESS),
							   ("MAN", "\"ssdp:discover\""),
							   ("MX", str(mx)),
							   ("ST", str(st))]))

class ResponseMessage(_Message):
	def __init__(self, maxAge, location, st, usn, t=time.gmtime()):
		headers = OrderedDict([("CACHE-CONTROL", "max-age - " + str(maxAge)),
							   ("DATE", formatDate(t)),
							   ("EXT", ""),
							   ("LOCATION", str(location)),
							   ("SERVER", USER_AGENT),
							   ("ST", str(st)),
							   ("USN", str(usn)),
							   ("BOOTID.UPNP.ORG", str(BOOT_ID)),
							   ("CONFIGID.UPNP.ORG", str(CONFIG_ID))])
		if SEARCH_PORT is not None:
			headers["SEARCHPORT.UPNP.ORG"] = str(SEARCH_PORT)
			
		_Message.__init__(self, "HTTP/1.1 200 OK", headers)

class AliveMessage(_NotifyMessage):
	def __init__(self, maxAge, location, nt, usn):
		headers = OrderedDict([("HOST", "%s:%d" % ADDRESS),
							   ("CACHE-CONTROL", "max-age - %d" % maxAge),
							   ("LOCATION", str(location)),
							   ("NT", str(nt)),
							   ("NTS", "ssdp:alive"),
							   ("SERVER", USER_AGENT),
							   ("USN", str(usn)),
							   ("BOOTID.UPNP.ORG", str(BOOT_ID)),
							   ("CONFIGID.UPNP.ORG", str(CONFIG_ID))])
		if SEARCH_PORT is not None:
			headers["SEARCHPORT.UPNP.ORG"] = str(SEARCH_PORT)
		
		_NotifyMessage.__init__(self, headers)

class UpdateMessage(_NotifyMessage):
	pass

class DeadMessage(_NotifyMessage):
	pass