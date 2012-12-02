from BeautifulSoup import BeautifulStoneSoup
import re

def HTMLToStoneSoup(response, selfClosingList=None):
	"""
	Input: HTTP Respnose (xml text)
	Output: BeautifulStoneSoup object 

	Notes: 	Code Search (grep) returns source code page with line numbers.  
			This method removes the line numbers before converting to soup.
	"""

	if response == None:
		return -1

	#From the source file, convert it to soup
	soup = None
	try:
		if selfClosingList != None:
			soup = BeautifulStoneSoup(response, convertEntities=BeautifulStoneSoup.HTML_ENTITIES, selfClosingTags=selfClosingList)
		else:
			#print "no self enclosing tags"
			soup = BeautifulStoneSoup(response, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)		
	except:
		print "Error: Stone Soup is cold"	

	pre = soup.find('pre')
	lines = re.compile('\d+\s').split(pre.contents[0]) #split a single string into multiple lines using regex
	xml_input = ''.join(lines) #join the separated lines back into a single input

	xml_soup = None
	try:
		if selfClosingList != None:
			xml_soup = BeautifulStoneSoup(str(xml_input), selfClosingTags=selfClosingList) 
		else:
			xml_soup = BeautifulStoneSoup(str(xml_input)) 	
	except:
		print "Error: xml soup is cold"

	return xml_soup
