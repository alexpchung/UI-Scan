import urllib2
from urlparse import urlparse
from urlparse import urljoin

class HttpAgent(object):
	"""HTTP connection"""
	def __init__(self, url):
		self.url = url
		self.proxyServer = '[Proxy Server Address]'

	def RequestResponse(self):
		proxy = urllib2.ProxyHandler({'http':self.proxyServer})
		opener = urllib2.build_opener(proxy)
		urllib2.install_opener(opener)
		request = urllib2.Request(self.url)
		response = urllib2.urlopen(request)

		return response