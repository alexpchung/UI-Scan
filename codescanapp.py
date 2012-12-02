""" Code Scan App using webpy 0.3 """

import web
from web import form

import threading
import Queue
from HttpAgent import HttpAgent
from SearchResult import SearchResult
from ADFBundle import ADFBundle
from ADFComponents import Dialog
from ADFComponents import Tag
from ADFComponents import CommandButton
from ADFComponents import Component
from BeautifulSoup import BeautifulSoup
from urlparse import urlparse
from urlparse import urljoin
import urllib
import time
import datetime

from DataTable import DataTable
import md5
from sets import Set
import re

###Settings
queue = Queue.Queue()
grepSource_url = "[URL of Target Source]"
today_date = datetime.datetime.today()
today_date_label = str(today_date.year) + str(today_date.month) + str(today_date.day)
tab = 'Home'

###url mappings
urls = (
	'/', 'index',
	'/dialog', 'Dialog',
	'/explore', 'Explore',
	'/explore2', 'Explore2',
	'/icon', 'Icon',
	'/progress', 'Progress',
	)

###Templates
t_globals = {
	'datestr':web.datestr,
	'tab':tab
}
render = web.template.render('templates', base='base', globals=t_globals)

###Processing Request
def startThreads(url, bundle_url, filename, param):
	elapsedTime = 0
	startTime = time.time()
	ADFBundle.grabBundleKeysByURL(bundle_url)

	print "processing... ", url 
	new_agent = HttpAgent(url)
	response = new_agent.RequestResponse()

	soup = BeautifulSoup(response)
	links = soup.findAll('a', {"target" : "_source"})

	mf = open("outputs/" + param['container'] + "MissingBundle_" + today_date_label + "_" + filename + ".txt", 'w')
	f = open("outputs/" + param['container'] + "SearchResults_" + today_date_label + "_" + filename + ".txt", 'w')
	bf = None

	if param['container'] == 'dialog':
		headerOutputLn = ["Page Link", "Product Family", "Dialog Number", "Dialog Title", "Dialog ID", "Dialog Modal", "Dialog Parents", "Button Group Name", "# of Command Buttons", "# of CANCEL", "# of OK", "# of DONE", "# of SAVE and CLOSE", "Component Name", "Component Attributes"]
		print >>f, '\t'.join(headerOutputLn)
	elif param['container'] == 'explore':
		headerOutputLn = ["Page Link", "Product Family", "Tag Number", "Tag Name", "Tag Parents", "Tag Attributes"]
		print >>f, '\t'.join(headerOutputLn)
	elif param['container'] == 'icon':
		headerOutputLn = ["Page Link", "Product Family", "Tag Number", "Tag Name", "Tag Parents", "Attribute Name", "File Extension", "Image Source", "Original Attribute Value"]
		print >>f, '\t'.join(headerOutputLn)

	#Create an instance for each search results
	parse_url = urlparse(response.geturl())
	hostname = parse_url.scheme + '://' + parse_url.netloc 

	for i in range(5):
		t = ThreadUrl(hostname, queue, mf, f, bf, param)
		t.setDaemon(True)
		t.start()

	counter = 0
	#populate queue with hosts
	for link in links:
		try:
			if param['processSize'] != 'All' and counter == int(param['processSize']):  #iterate over only a few for testing purpose
				break
		except:
			pass	

		counter += 1
		#Add to queue			
		queue.put(link)

	#wait on queue until everything has been processed
	queue.join()

	f.close()
	mf.close()	
	elapsedTime = (time.time() - startTime)
	print "Elapsed Time: %s" % Icon.elapsedTime
	return elapsedTime

###Record Session Data
def recordSession(param, sessionKey, searchType):
	dataFilename = "shelve/codeScanTable" #persistent dictionary that will hold the CodeScan records
	dataTable = DataTable(dataFilename)	#establish connection to the persistent dataTable
	
	rowData = dict()
	rowData['runDate'] = str(today_date)
	rowData['searchType'] = searchType
	rowData['sessionKey'] = sessionKey
	rowData['elapsedTime'] = ''
	try:
		if param['elapsedTime'] is not None:
			rowData['elapsedTime'] = param['elapsedTime']		
	except:
		pass
	rowData['top'] = ''
	try:
		if param['top'] is not None:
			rowData['top'] = param['top']	
	except:
		pass
	rowData['series'] = ''
	try:
		if param['series'] is not None:
			rowData['series'] = param['series']	
	except:
		pass
	rowData['label'] = ''
	try:
		if param['label'] is not None:
			rowData['label'] = param['label']	
	except:
		pass
	rowData['command'] = ''
	try:
		if param['command'] is not None:
			rowData['command'] = param['command']	
	except:
		pass
	rowData['commandArgument'] = ''
	try:
		if param['commandArgument'] is not None:
			rowData['commandArgument'] = param['commandArgument']	
	except:
		pass
	rowData['files'] = ''
	try:
		if param['files'] is not None:
			rowData['files'] = param['files']	
	except:
		pass
	rowData['contents'] = ''
	try:
		if param['contents'] is not None:
			rowData['contents'] = param['contents']	
	except:
		pass
	rowData['processSize'] = ''
	try:
		if param['processSize'] is not None:
			rowData['processSize'] = param['processSize']	
	except:
		pass
	rowData['container'] = ''
	try:
		if param['container'] is not None:
			rowData['container'] = param['container']	
	except:
		pass
	rowData['title'] = ''
	try:
		if param['title'] is not None:
			rowData['title'] = param['title']	
	except:
		pass
	rowData['commandButton'] = ''
	try:
		if param['commandButton'] is not None:
			rowData['commandButton'] = param['commandButton']	
	except:
		pass
	rowData['componentName'] = ''
	try:
		if param['componentName'] is not None:
			rowData['componentName'] = param['componentName']	
	except:
		pass
	rowData['tag'] = ''
	try:
		if param['tag'] is not None:
			rowData['tag'] = param['tag']	
	except:
		pass
	rowData['attribute'] = ''
	try:
		if param['attribute'] is not None:
			rowData['attribute'] = param['attribute']	
	except:
		pass
	rowData['attribute_value'] = ''
	try:
		if param['attribute_value'] is not None:
			rowData['attribute_value'] = param['attribute_value']	
	except:
		pass

	rowNum = dataTable.insertRow(rowData)

	dataTable.closeTable() #close the file connection

###Transform HTML Selection Options into a list
def getFormSelection(select):
	option_list = list()

	options = select.findAll('option')
	for option in options:
		#option_list.append("\"" + str(option['value']) + "\"" + ":" + "\"" + str(option.string) + "\"")
		select = 0
		if option.has_key('selected'):
			select = 1
		
		#option_dict[str(option['value'])] = str(option.string) + ":" + str(select)
		option_list.append((str(option['value']), str(option.string)))

	return option_list

###Get From Parameters from Search Source @ [URL of Target Source]
def retrieveFormParam():
	option_dict = dict()

	new_agent = HttpAgent(grepSource_url)
	if new_agent:
		response = new_agent.RequestResponse()

		soup = BeautifulSoup(response)
		#Find top selection
		app = soup.find('select', attrs={"name":"top"})	
		app_options = getFormSelection(app)
		option_dict['app_options'] = app_options

		#Find series selection
		series = soup.find('select', attrs={"name":"series"})
		series_options = getFormSelection(series)
		option_dict['series_options'] = series_options

		#Find label selection
		"""
		#Failed to link this dropdown list to series selection
		label = soup.find('select', attrs={"name":"label"})
		label_options = getFormSelection(label)  
		option_dict['label_options'] = label_options
		"""
		label_options = ['LATEST']
		option_dict['label_options'] = label_options

		#Find cmd selection
		cmd = soup.find('select', attrs={"name":"cmd"})
		cmd_options = getFormSelection(cmd)
		option_dict['cmd_options'] = cmd_options		
	else:
		print "no agent is established"

	return option_dict

###Index Table of Previous Scans
def getAllScans():
	dataFilename = "shelve/codeScanTable" #persistent dictionary that will hold the CodeScan records
	dataTable = DataTable(dataFilename)	#establish connection to the persistent dataTable
	
	scan_list = list()
	scan_list = dataTable.getAllRows()

	print scan_list

	dataTable.closeTable() #close the file connection
	
	return scan_list

###Threading Classes
class Query(object):
	"""Query Parameters"""
	def __init__(self, top=None, series=None, label=None, cmd=None, cmdArg=None, filespec=None, contents=None, displayResults=None):
		super(Query, self).__init__()
		self.top = top
		if self.top:
			self.top = urllib.quote(self.top, '')
		self.series = series
		self.label = label
		self.cmd = cmd
		self.cmdArg = cmdArg
		self.filespec = filespec
		self.contents = contents
		self.displayResults = displayResults

	def generateSearchSourceURL(self):
		url = grepSource_url + "?top=" + self.top + "&series=" + self.series + "&label=" + self.label + "&cmd=" + self.cmd + "&cmdArg=" + self.cmdArg + "&filespec=" + self.filespec + "&contents=" + self.contents + "&Search=Search"
		return url

	def generateBundleIndexURL(self):
		bundleUrl = grepSource_url + "?top=" + self.top + "&series=" + self.series + "&label=" + self.label + "&cmd=" + self.cmd + "&cmdArg=" + self.cmdArg + "&filespec=*Bundle.xlf*" + "&contents=" + "&Search=Search"
		return bundleUrl

class ThreadUrl(threading.Thread):
	def __init__(self, hostname, queue, mf=None, f=None, bf=None, param=None):
		threading.Thread.__init__(self)
		self.hostname = hostname
		self.queue = queue
		self.mf = mf
		self.f = f
		self.bf = bf
		self.param = param

	def runDialogSearch(self, new_searchResult):
		dialogs = new_searchResult.searchDialogs()
		if dialogs:
			for dialog in dialogs:
				##Extract Dialog Title
				print "dialog title:", dialog.title
				newDialogTitle = new_searchResult.extractTitle(dialog.title)
				dialog.source = newDialogTitle	
				#Search for af:CommandButtons in dialog
				try:
					component_list = new_searchResult.searchComponents(dialog.soup, "af:dialog", 'af:commandbutton')
					for component in component_list:
						dialog.addCommandButton(component)
						print "Add commandButton"
				except:
					print "No command button is found in dialog"

				#Search for Others if specified
				if self.param['components']:
					for c in self.param['components']:
						try:
							component_list = new_searchResult.searchComponents(dialog.soup, "af:dialog", c)
							for component in component_list:
								dialog.addComponent(component)
						except:
							print "No component with name:", c, " is found in dialog"

			print "number of dialogs:", len(dialogs)				
			new_searchResult.printDialogs(dialogs, self.f, self.bf)

	def runPageSearch(self, new_searchResult, tagAfKey=None, attrDict=None):
		tags = new_searchResult.searchTags(tagAfKey, attrDict)

		print "search tagAfKey:", tagAfKey
		if attrDict is None:
			attrDict = dict()

		print "search attrDict:", attrDict

		if tags:
			for tag in tags:
				tagName = tag.tagName	

				#if attrDict:
				if tag.sourceAttrs:					
					#Attributes Provided																		
					for key, value in tag.sourceAttrs:
						try:							
							if value != '':
								tag.attrs[(key)] = new_searchResult.extractTitle(value)	
							else:
								tag.attrs[(key)] = None
						except:
							print "attribute value extraction error"		
							tag.attrs[(key)] = None													
			try:				
				new_searchResult.printTags(tags, self.f, self.bf)
			except:
				print "tag printing error"

	def runIconSearch(self, new_searchResult):
		#Look up all the tag components within a page
		tags = new_searchResult.searchTags()
		#Regex for image file
		imageExtPattern = re.compile('\.(?:png|gif|jpg|jpeg|bmp)')
		imagePathPattern = re.compile('([\w|/]+\.(?:png|gif|jpg|jpeg|bmp))')

		#A list of tags containing icons
		imageTags = list()

		if tags:
			for tag in tags:
				tagName = tag.tagName
				
				if tag.sourceAttrs:
					for key, value in tag.sourceAttrs:
						try:
							if value != '':
								tag.attrs[(key)] = new_searchResult.extractTitle(value)	
							else:
								tag.attrs[(key)] = None

							#Check for image file extension	
							if re.search(imageExtPattern, value):
								attrName = key
								imagePath = value

								#Find all images
								match = re.findall(imagePathPattern, value)
								if match:
									for m in match:
										tag.image_list.append((attrName,m))
						except:
							pass

				#Add tag to imageTags list if the tag has image
				if tag.image_list:
					print "image list found:", len(tag.image_list)
					imageTags.append(tag)			

			try:
				new_searchResult.printTagImages(imageTags, self.f, self.bf)
			except:
				print "image search error"				

	def run(self):
		while True:
			#grab url from queue
			link = self.queue.get()
			print "link href:", link['href']

			try:
				new_searchResult = SearchResult(self.hostname, link['href'], None)				
				new_searchResult.searchSource() #Get the CSet variables		
				new_searchResult.grabBundleSource(self.mf) #Grab the Bundle Resources	

				#Container
				if self.param['container'] == 'dialog':
					###Search for Dialogs
					self.runDialogSearch(new_searchResult)						

				elif self.param['container'] == 'page':
					#Page
					tagAfKey = "af:panelgrouplayout"
					self.runPageSearch(new_searchResult, tagAfKey)						

				elif self.param['container'] == 'explore':
					#Generic Search
					tagName = None

					if self.param['tag'] != 'All':
						print "tag:", self.param['tag']
						tagName = self.param['tag']

					attr_dict = dict()
					if self.param['attribute'] != 'All':
						print "attributeA:", self.param['attribute']

						if self.param['attribute_value'] is not None:
							print "value:", self.param['attribute_value']

							attr_dict[(self.param['attribute'])] = self.param['attribute_value']
						else:
							print "value: compile"

							attr_dict[(self.param['attribute'])] = re.compile(".+")

						self.runPageSearch(new_searchResult, tagName, attr_dict)
					else:
						self.runPageSearch(new_searchResult, tagName)
				elif self.param['container'] == 'icon':
					#Icons
					self.runIconSearch(new_searchResult)
				
				print "successful"

				#print Output to Files
			except:
				print "unsuccessful"
				pass

			#signals to queue job is done
			self.queue.task_done()

###Dynamic Web Forms
class DynamicForm(form.Form):
		
	def add_input(self, new_input):
		list_inputs = list(self.inputs)
		if new_input is not None:
			self.inputs = tuple(list_inputs + [new_input, ])

###Index Page
class index:
	def GET(self):
		""" Show Homepage """
		scans = getAllScans()
		return render.index(scans)

###Progress Bar
class Progress:
	def GET(self):
		return render.progress(None)

###Dialog Search Entry Form
class Dialog:
	option_dict = dict()
	elapsedTime = 0

	def defineFormInputs(self, myform):
		myform.add_input(form.Dropdown("top", Dialog.option_dict['app_options']))
		myform.add_input(form.Dropdown("series", Dialog.option_dict['series_options']))
		myform.add_input(form.Dropdown("label", Dialog.option_dict['label_options']))
		myform.add_input(form.Dropdown("command", Dialog.option_dict['cmd_options']))
		myform.add_input(form.Textbox("commandArgument"))
		myform.add_input(form.Textbox("files"))
		#myform.add_input(form.Textbox("contents"))

		#myform.add_input(form.Dropdown("container", ['dialog', 'page', 'all']))
		#myform.add_input(form.Checkbox('title', value="Y", checked=True))
		myform.add_input(form.Checkbox('commandButton', value="Y", checked=True, disabled=True))
		myform.add_input(form.Checkbox('otherComponent', value="Y", checked=False))
		myform.add_input(form.Textbox("otherComponentName"))
		myform.add_input(form.Dropdown("processSize", [5, 10, 50, 100, 'All'], value='All'))

	def GET(self):
		
		#Retrieve the search parameters from Code Search WebPage
		Dialog.option_dict = retrieveFormParam()
		 
		myform = DynamicForm()
		self.defineFormInputs(myform)

		#make sure you create a copy of the form by calling it (line above)
		#Otherwise changes will appear globally
		return render.formtest(myform)

	def POST(self):
		myform = DynamicForm()
		self.defineFormInputs(myform)

		if not myform.validates():
			return render.formtest(myform)
		else:
			#form.d.boe and form['boe'].value are same ways of
			#extracting the validated arguments from the form.

			#Build the URL for GrepTool
			new_query = Query(myform['top'].value, myform['series'].value, myform['label'].value, myform['command'].value, myform['commandArgument'].value, myform['files'].value, 'af:dialog')
			
			#Set up the parameters
			param = dict()
			param['container'] = 'dialog'
			#features = list()
			components = list()
			"""
			if (myform['title'].checked):
				features.append('title')
			if (myform['commandButton'].checked):
				features.append('commandButton')
			"""
			if (myform['otherComponent'].checked and myform['otherComponentName'].value != ''):
				components.append(myform['otherComponentName'].value)				
			#param['features'] = features
			param['components'] = components
			param['processSize'] = myform['processSize'].value

			new_url = new_query.generateSearchSourceURL()	
			m = md5.new(str(today_date)) #create an unique key for the filename
			m.update(new_url) #update the unique key's parameters
			sessionKey = m.hexdigest()

			#Instance that holds the dictionary for adfbundle key to the bundle's source
			bundle_url = new_query.generateBundleIndexURL()		

			"""
			Start the Code Scanning
			"""
			Dialog.elapsedTime = startThreads(new_url, bundle_url, sessionKey, param)

			"""
			Record this session into the DataTable
			"""
			param['elapsedTime'] = Dialog.elapsedTime
			param['top'] = myform['top'].value
			param['series'] = myform['series'].value
			param['label'] = myform['label'].value
			param['command'] = myform['command'].value
			param['commandArgument'] = myform['commandArgument'].value
			param['files'] = myform['files'].value
			#param['contents'] = 'af:dialog'
			#param['title'] = myform['title'].checked
			param['commandButton'] = myform['commandButton'].checked			
			if components:
				param['componentName'] = ','.join(components)
			else:
				param['componentName'] = ''

			recordSession(param, sessionKey, 'Dialog')

			#Return back to front page with scan history
			raise web.seeother('/')
			
###Explore labels
class Explore:
	option_dict = dict()
	exploreQueue = Queue.Queue()
	allTags = Set()
	allAttrs = Set()

	def defineFormInputs(self, myform):
		myform.add_input(form.Dropdown("top", Explore.option_dict['app_options']))
		myform.add_input(form.Dropdown("series", Explore.option_dict['series_options']))
		myform.add_input(form.Dropdown("label", Explore.option_dict['label_options']))
		myform.add_input(form.Dropdown("command", Explore.option_dict['cmd_options']))
		myform.add_input(form.Textbox("commandArgument"))
		myform.add_input(form.Textbox("files"))
		myform.add_input(form.Textbox("contents"))		

	def startThreads(self, url, bundle_url):
		startTime = time.time()		
		ADFBundle.grabBundleKeysByURL(bundle_url)

		print "processing... ", url 
		new_agent = HttpAgent(url)
		response = new_agent.RequestResponse()

		#Read only the first 1MB of data
		snippet = response.read(50000)

		soup = BeautifulSoup(snippet)
		links = soup.findAll('a', {"target" : "_source"})

		#Create an instance for each search results
		parse_url = urlparse(response.geturl())
		hostname = parse_url.scheme + '://' + parse_url.netloc 

		counter = 0
		#populate queue with hosts
		for link in links:			
			counter += 1

			try:
				new_searchResult = SearchResult(hostname, link['href'], None)				
				newTags, newAttrs = new_searchResult.exploreSource() #Get the CSet variables		
				
				Explore.allTags = Explore.allTags.union(newTags)
				Explore.allAttrs = Explore.allAttrs.union(newAttrs)
			except:
				print "link unexplored"
				pass

		elapsedTime = (time.time() - startTime)
		print "Elapsed Time: %s" % elapsedTime

	def GET(self):
		Explore.option_dict = retrieveFormParam()

		myform = DynamicForm()
		self.defineFormInputs(myform)

		return render.formexplore(myform)

	def POST(self):
		myform = DynamicForm()
		self.defineFormInputs(myform)

		if not myform.validates():
			return render.formexplore(myform)
		else:
			f = open("exploreFormInputs.txt", 'w')
			f.write("top:" + myform['top'].value)		
			f.write('\n')	
			f.write("series:" + myform['series'].value)
			f.write('\n')
			f.write("label:" + myform['label'].value)
			f.write('\n')	
			f.write("command:" + myform['command'].value)
			f.write('\n')	
			f.write("commandArgument:" + myform['commandArgument'].value)
			f.write('\n')	
			f.write("files:" + myform['files'].value)
			f.write('\n')	
			f.write("contents:" + myform['contents'].value)
			f.write('\n')	
		
			#Build the URL for GrepTool
			new_query = Query(myform['top'].value, myform['series'].value, myform['label'].value, myform['command'].value, myform['commandArgument'].value, myform['files'].value, myform['contents'].value)
			new_url = new_query.generateSearchSourceURL()	
			#Instance that holds the dictionary for adfbundle key to the bundle's source
			bundle_url = new_query.generateBundleIndexURL()		

			"""
			Start the Code Scanning
			"""			
			self.startThreads(new_url, bundle_url)

			f.write("tags:" + ','.join(list(Explore.allTags)))
			f.write('\n')
			f.write("attrs:" + ','.join(list(Explore.allAttrs)))
			f.write('\n')
			print "allTags:", Explore.allTags
			print "allAttrs:", Explore.allAttrs

			f.close()

			raise web.redirect('/explore2')

class Explore2:
	option_dict = dict()
	prevForm_dict = dict()
	elapsedTime = 0

	def defineFormInputs(self, myform):
		myform.add_input(form.Dropdown("tag_selection", ['All'] + sorted(self.prevForm_dict['tags'].split(','))))
		myform.add_input(form.Dropdown("attribute_selection", ['All'] + sorted(self.prevForm_dict['attrs'].split(','))))

		myform.add_input(form.Textbox("tag_name"))
		myform.add_input(form.Textbox("attribute_name"))

		myform.add_input(form.Textbox("attribute_value"))
		myform.add_input(form.Dropdown("processSize", [5, 10, 50, 100, 'All'], value='All'))

	def GET(self):
		f = open("exploreFormInputs.txt", 'r')
		for line in f:
			line = line.strip()
			(key, value) = line.split(':', 1)
			self.prevForm_dict[key] = value #parameters from previous form
		f.close()

		myform = DynamicForm()
		self.defineFormInputs(myform)
		
		return render.formexplore(myform)

	def POST(self):
		myform = DynamicForm()
		self.defineFormInputs(myform)

		if not myform.validates():
			return render.formexplore(myform)
		else:
			#Build the URL for GrepTool
			new_query = Query(self.prevForm_dict['top'], self.prevForm_dict['series'], self.prevForm_dict['label'], self.prevForm_dict['command'], self.prevForm_dict['commandArgument'], self.prevForm_dict['files'], self.prevForm_dict['contents'])
			new_url = new_query.generateSearchSourceURL()	
			#Instance that holds the dictionary for adfbundle key to the bundle's source
			bundle_url = new_query.generateBundleIndexURL()		

			param = dict()
			param['container'] = 'explore'

			##Search by Tag Name
			if myform['tag_name'].value != '':
				param['tag'] = myform['tag_name'].value
			else:
				param['tag'] = myform['tag_selection'].value

			##Search by Attribute Name
			if myform['attribute_name'].value != '':
				param['attribute'] = myform['attribute_name'].value
			else:
				param['attribute'] = myform['attribute_selection'].value

			if myform['attribute_value'].value != '':
				param['attribute_value'] = myform['attribute_value'].value
			else:
				param['attribute_value'] = None

			param['processSize'] = myform['processSize'].value

			new_url = new_query.generateSearchSourceURL()	
			m = md5.new(str(today_date)) #create an unique key for the filename
			m.update(new_url) #update the unique key's parameters
			sessionKey = m.hexdigest()

			#Instance that holds the dictionary for adfbundle key to the bundle's source
			bundle_url = new_query.generateBundleIndexURL()		

			"""
			Start the Code Scanning
			"""
			Explore2.elapsedTime = startThreads(new_url, bundle_url, sessionKey, param)

			"""
			Record this session into the DataTable
			"""
			param['elapsedTime'] = Explore2.elapsedTime
			param['top'] = self.prevForm_dict['top']
			param['series'] = self.prevForm_dict['series']
			param['label'] = self.prevForm_dict['label']
			param['command'] = self.prevForm_dict['command']
			param['commandArgument'] = self.prevForm_dict['commandArgument']
			param['files'] = self.prevForm_dict['files']
			param['contents'] = self.prevForm_dict['contents']
	
			recordSession(param, sessionKey, 'Explore')

			raise web.seeother('/')

class Icon:
	option_dict = dict()
	elapsedTime = 0

	def defineFormInputs(self, myform):
		myform.add_input(form.Dropdown("top", Icon.option_dict['app_options']))
		myform.add_input(form.Dropdown("series", Icon.option_dict['series_options']))
		myform.add_input(form.Dropdown("label", Icon.option_dict['label_options']))
		myform.add_input(form.Dropdown("command", Icon.option_dict['cmd_options']))
		myform.add_input(form.Textbox("commandArgument"))
		myform.add_input(form.Textbox("files"))
		myform.add_input(form.Textbox("contents"))
		myform.add_input(form.Dropdown("processSize", [5, 10, 50, 100, 'All'], value='All'))

	def GET(self):
		Icon.option_dict = retrieveFormParam()

		myform = DynamicForm()
		self.defineFormInputs(myform)

		return render.formicon(myform)

	def POST(self):
		myform = DynamicForm()
		self.defineFormInputs(myform)

		if not myform.validates():
			return render.formicon(myform)
		else:
			#form.d.boe and form['boe'].value are same ways of
			#extracting the validated arguments from the form.

			#Build the URL for GrepTool
			new_query = Query(myform['top'].value, myform['series'].value, myform['label'].value, myform['command'].value, myform['commandArgument'].value, myform['files'].value, myform['contents'].value)
			
			#print "container:", myform['container'].value, " title:", myform['title'].checked, " button:", myform['commandButton'].checked
			#Set up the parameters
			param = dict()
			param['container'] = 'icon'
			#features = list()
			#features.append('icon')	
			#param['features'] = features
			param['processSize'] = myform['processSize'].value

			new_url = new_query.generateSearchSourceURL()	
			m = md5.new(str(today_date)) #create an unique key for the filename
			m.update(new_url) #update the unique key's parameters
			sessionKey = m.hexdigest()

			#Instance that holds the dictionary for adfbundle key to the bundle's source
			bundle_url = new_query.generateBundleIndexURL()		

			"""
			Start the Code Scanning
			"""
			Icon.elapsedTime = startThreads(new_url, bundle_url, sessionKey, param)

			"""
			Record this session into the DataTable
			"""
			param['elapsedTime'] = Icon.elapsedTime
			param['top'] = myform['top'].value
			param['series'] = myform['series'].value
			param['label'] = myform['label'].value
			param['command'] = myform['command'].value
			param['commandArgument'] = myform['commandArgument'].value
			param['files'] = myform['files'].value
			param['contents'] = myform['contents'].value
			
			recordSession(param, sessionKey, 'Icon')

			raise web.seeother('/')


######################################
app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()