import Soup
from HttpAgent import HttpAgent
import re
from urlparse import urlparse

class ADFBundle(object):
	"""ADFBundle instance holding all key and value pairs for adfBundle"""
	bundleAddress = dict()
	bundleSoup = dict()

	@staticmethod
	def grabBundleKeys(inputFile):
		with open(inputFile, 'r') as f_bundle:
			while True:
				line = f_bundle.readline()
				line = line.strip()
				if not line:
					break

				bundleKey, bundleLink = line.split('\t')

				#Build the hash key from "oracle/apps/" to the end
				oracleAppPattern = re.compile('oracle/apps')
				if re.search(oracleAppPattern, bundleKey):
					key = bundleKey.split('oracle/apps')[1]
					key = re.sub('/', '.', key)
					key = 'oracle.apps' + key
				else:
					key = re.sub('/', '.', bundleKey)

				ADFBundle.bundleAddress[key] = bundleLink				

		f_bundle.close()

	@staticmethod
	def grabBundleKeysByURL(url):
		new_agent = HttpAgent(url)
		response = new_agent.RequestResponse()
		htmlBody = response.read()

		parse_url = urlparse(response.geturl())
		hostname = parse_url.scheme + '://' + parse_url.netloc 

		linksBody = htmlBody.split('<a', 1)

		if linksBody:
			links = linksBody[1].split('+')

			hrefPattern = re.compile('_source\"\s?href=\"([\w.:/\&-_\?\;]+\.xlf)\">([\w./&\-_]+)')
			for link in links:
				if re.search('_source', link):
					found = re.search(hrefPattern, link)

					#folders = found.group(2).split('/')
					#bundleSet.add(folders[-1])
					#print link
					#print found.group(1)
					bundleKey = found.group(2)
					bundleKey = re.sub('</a>', '', bundleKey)
					bundleKey = re.sub('.xlf', '', bundleKey)
					
					bundleLink = hostname + found.group(1)

					#Build the hash key from "oracle/apps/" to the end
					oracleAppPattern = re.compile('oracle/apps')
					if re.search(oracleAppPattern, bundleKey):
						key = bundleKey.split('oracle/apps')[1]
						key = re.sub('/', '.', key)
						key = 'oracle.apps' + key
					else:
						key = re.sub('/', '.', bundleKey)

					#print "key:", key, " link:", bundleLink
					ADFBundle.bundleAddress[key] = bundleLink
			print str(len(links))

	@staticmethod
	def grabBundleSource(key):
		if key not in ADFBundle.bundleSoup:
			print "key:", key
			try:
				if ADFBundle.bundleAddress[key] != None:
					url = ADFBundle.bundleAddress[key] + '&content=1'
					try:
						new_agent = HttpAgent(url)
						if new_agent:
							response = new_agent.RequestResponse()
						else:
							print "no agent is established"
					except:
						print "Error: Cannot establish http agent"
				
					#From the source file, convert it to soup
					xliff_soup = None
					try:
						xliff_soup = Soup.HTMLToStoneSoup(response, None)
					except:
						print "Error: Cannot convert http response into soup"
					
					#Save the soup object for all the dialogs within the JSF
					ADFBundle.bundleSoup[(key)] = xliff_soup
			except:
				print "key is not found in bundleAddress"
		else:
			print "key is already in bundleSoup"
			pass