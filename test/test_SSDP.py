'''
Created on Aug 4, 2013

@author: Jonathan
'''
import SSDP

import unittest

def compareMessages(original, assertion):
	if original[0] != assertion[0]: return False
	for key in assertion[1]:
		if key not in original[1]:
			return False
		if original[1][key] != assertion[1][key]:
			return False
	return True

class SSDPAssert(object):
	def __init__(self):
		self._assertions = []
	
	def addAssert(self, method, headers):
		self._assertions.append((method, headers))
		
	def verify(self, messages):
		assertions = self._assertions
		for message in messages:
			messageData = SSDP.parseMessage(message)
			for assertion in assertions:
				if compareMessages(messageData, assertion):
					assertions.remove(assertion)
					break
			else:
				return False
		return len(assertions) == 0

class Test_Device(unittest.TestCase):

	def test_updateBootId_bootIdDifferent(self):
		device = SSDP.Device("fake", "fake")
		initialBootId = device.bootId
		device.updateBootId()
		self.assertNotEqual(initialBootId, device.bootId)
		
	def test_updateBootId_bootIdRollOverAtMax(self):
		device = SSDP.Device("fake", "fake", bootId=2**31 - 1)
		device.updateBootId()
		self.assertEqual(0, device.bootId)
		
	def test_constructor_bootIdn1_ThrowValueError(self):
		self.assertRaises(ValueError, lambda: SSDP.Device("fake", "fake", bootId=-1))
		
	def test_constructor_bootId2p31_ThrowValueError(self):
		self.assertRaises(ValueError, lambda: SSDP.Device("fake", "fake", bootId=2**31))
		
	def test_constructor_configIdn1_ThrowValueError(self):
		self.assertRaises(ValueError, lambda: SSDP.Device("fake", "fake", configId=-1))
		
	def test_constructor_configId2p24_ThrowValueError(self):
		self.assertRaises(ValueError, lambda: SSDP.Device("fake", "fake", configId=2**24))
		
class Test_renderAliveMessages(unittest.TestCase):
	
	def test_rootDeviceWithChildDeviceAndServiceWithChildService(self):
		root = SSDP.Device("thisisauuid1", "thisisaurn1", location="127.0.0.1", bootId=0)
		childDevice = SSDP.Device("thisisauuid2", "thisisaurn2", bootId=1)
		childDevice.addService(SSDP.Service("thisisaserviceurn1"))
		root.addDevice(childDevice)
		root.addService(SSDP.Service("thisisaserviceurn2"))
		
		ssdpAssert = SSDPAssert()
		ssdpAssert.addAssert("NOTIFY * HTTP/1.1", {"NTS": "ssdp:alive",
													"CACHE-CONTROL": "max-age - 5",
													"LOCATION": "127.0.0.1",
													"NT": "upnp:rootdevice",
													"USN": "uuid:thisisauuid1::upnp:rootdevice",
													"BOOTID.UPNP.ORG": "0"})
		ssdpAssert.addAssert("NOTIFY * HTTP/1.1", {"NTS": "ssdp:alive",
													"CACHE-CONTROL": "max-age - 5",
													"LOCATION": "127.0.0.1",
													"NT": "uuid:thisisauuid1",
													"USN": "uuid:thisisauuid1",
													"BOOTID.UPNP.ORG": "0"})
		ssdpAssert.addAssert("NOTIFY * HTTP/1.1", {"NTS": "ssdp:alive",
													"CACHE-CONTROL": "max-age - 5",
													"LOCATION": "127.0.0.1",
													"NT": "urn:thisisaurn1",
													"USN": "uuid:thisisauuid1::urn:thisisaurn1",
													"BOOTID.UPNP.ORG": "0"})
		ssdpAssert.addAssert("NOTIFY * HTTP/1.1", {"NTS": "ssdp:alive",
													"CACHE-CONTROL": "max-age - 5",
													"LOCATION": "127.0.0.1",
													"NT": "uuid:thisisauuid2",
													"USN": "uuid:thisisauuid2",
													"BOOTID.UPNP.ORG": "0"})
		ssdpAssert.addAssert("NOTIFY * HTTP/1.1", {"NTS": "ssdp:alive",
													"CACHE-CONTROL": "max-age - 5",
													"LOCATION": "127.0.0.1",
													"NT": "urn:thisisaurn2",
													"USN": "uuid:thisisauuid2::urn:thisisaurn2",
													"BOOTID.UPNP.ORG": "0"})
		ssdpAssert.addAssert("NOTIFY * HTTP/1.1", {"NTS": "ssdp:alive",
													"CACHE-CONTROL": "max-age - 5",
													"LOCATION": "127.0.0.1",
													"NT": "urn:thisisaserviceurn1",
													"USN": "uuid:thisisauuid2::urn:thisisaserviceurn1",
													"BOOTID.UPNP.ORG": "0"})
		ssdpAssert.addAssert("NOTIFY * HTTP/1.1", {"NTS": "ssdp:alive",
													"CACHE-CONTROL": "max-age - 5",
													"LOCATION": "127.0.0.1",
													"NT": "urn:thisisaserviceurn2",
													"USN": "uuid:thisisauuid1::urn:thisisaserviceurn2",
													"BOOTID.UPNP.ORG": "0"})
		
		messages = SSDP.renderAliveMessages(root, maxAge=5)
		self.assertTrue(ssdpAssert.verify(messages))

if __name__ == "__main__":
	unittest.main()