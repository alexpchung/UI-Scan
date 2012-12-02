import Soup
from HttpAgent import HttpAgent
from ADFBundle import ADFBundle
from ADFComponents import Dialog
from ADFComponents import CommandButton
from ADFComponents import Component
from ADFComponents import Tag
from urlparse import urlparse
from urlparse import urljoin
import re
from sets import Set
import os

class SearchResult(object):
	"""Query Search Results"""	

	def __init__(self, hostname=None, target=None, counter=None):
		self.target = target
		self.hostname = hostname
		self.counter = counter
		self.dialog_list = list()
		self.bundlePathDict = dict()
		self.bundlePathSoup = dict()
		self.bundlePathURL = dict()

		self.resultSoup = None

	def getTargetFullPath(self):
		"""<a target=\"_source\" href=
		Set source with full url path"""

		#if href begins with '/', rebuild the full URL
		if self.target[0] == '/':
			self.target = urljoin(self.hostname, self.target)
		else:
			self.target = self.target
		self.target += "&content=1"
		return self.target

	def getFolderStructure(self):
		#Extract the folder structure starting from oracle/app/
		oracleAppPattern = '(/oracle/apps[\w|/]+)\.'
		match = re.search(oracleAppPattern, self.target)
		if match:
			folderStruc = match.group(1)
		else:
			folderStruc = ''
		return folderStruc

	def grabBundleSource(self, mf):
		"""The <c:set> points to an adfBundle.  This function go directly to the source of these bundles"""

		#adfBundle precompile a list of adfBundle keys pointing to their respective URLs		
		valueHashPattern = re.compile('^#\{(\w+)\[\'([\w.]+)\'\]\}')
		
		for key, value in self.bundlePathDict.items():
			#Transform the bundle value to a directory path
			match = re.match(valueHashPattern, value)
			if match:
				adfBundleDictName = match.group(1) #adfBundle
				adfBundleKey = match.group(2) #oracle.apps.atk.essMeta.resource.AtkEssMetaEHBundle   	
				
				try:
					if ADFBundle.bundleSoup[adfBundleKey] != None:  #grab bundle source if already defined						
						self.bundlePathURL[(key)] = ADFBundle.bundleAddress[adfBundleKey]
						self.bundlePathSoup[(key)] = ADFBundle.bundleSoup[(adfBundleKey)]							
					else:
						print "bundleSoup does not exist"
				except:						
					try:
						if ADFBundle.bundleAddress[adfBundleKey]:
							#url = ADFBundle.bundleAddress[adfBundleKey] + '&content=1'
							self.bundlePathURL[(key)] = ADFBundle.bundleAddress[adfBundleKey]
							try:
								ADFBundle.grabBundleSource(adfBundleKey)
								#Save the soup object for all the dialogs within the JSF
								self.bundlePathSoup[(key)] = ADFBundle.bundleSoup[(adfBundleKey)]
							except:
								print "ADFBundle cannot be created"
					except:
						print "Sorry, this bundle key is not recognized"
						print >>mf, adfBundleKey	
				finally:
					print adfBundleKey, " scanned"	

	def extractTitle(self, title):
		"""
		Extract the title from within the #{...}
		Check for the bundle key/value in hash syntax: key[value]
		Look up the key in bundle definition in c:set tags
		If bundle definition is found, find the key in bundle resource marked as trans_unit
		Replace the original title with the display value from the bundle file
		"""

		conditionPattern = re.compile('(.+?\s*\?\s*.*?\s*:\s*.+)')
		colonRangePattern = re.compile('\{\'\s*:\s*\'\}')
		colonPattern = re.compile(':')
		doubledashRangePattern = re.compile('--\s*#\s?{')
		dashRangePattern = re.compile('-\s*#\s*{')
		questionPattern = re.compile('\?')

		valueHashPattern = re.compile('(#\{.+?\})')
		badCharPattern = re.compile('#\{(.+)\}')

		hashPattern = re.compile('\w+\[\'[\w.]+\'\]')
		hashGroupPattern = re.compile('(\w+)\[\'([\w.]+)\'\]')

		new_title = title	
		title_notes = list()
		bundleURLs = list()

		match = re.findall(valueHashPattern, title)
		if match:
			for m in match:					
				insideBracket = re.search(badCharPattern, m)
				m_edit = insideBracket.group(1)
				new_title = new_title.replace(m, m_edit)

				moreMatch = re.findall(hashPattern, m_edit)
				found = 0
				try:					
					if len(moreMatch) > 0:
						for h in moreMatch:
							hashMatch = re.search(hashGroupPattern, h)
							try:
								cset_key = hashMatch.group(1) #atkessmetadatapublicuiBundle1
								transUnit_key = hashMatch.group(2) #'Header.CreateQuestionGroup.CreateAssessmentTemplateQuesti'
								
								if self.bundlePathSoup[cset_key]:
									xliff_soup = self.bundlePathSoup[cset_key] 
									trans_unit = xliff_soup.find('trans-unit', {"id" : transUnit_key})
									
									if trans_unit:
										source = trans_unit.find('source')
										notes = trans_unit.findAll('note')
										try:								
											new_title = new_title.replace(h, source.string)	
											found = 1			

											if notes:
												title_notes.append(notes)					
											bundleURLs.append(self.bundlePathURL[(cset_key)])

											#if notes:	
											#	title_notes = ';'.join([re.sub(r'[\t\n]+', ' ', c.string) for c in notes])		
											#bundleURLs.append(self.bundlePathURL[(cset_key)])		
										except:
											print "No source is found for title: " + transUnit_key
									else:
										print "No trans_unit found"
									
							except:
								print "key is not found in cset bundle"
								pass
				except:
					pass
			
		return new_title

	def searchComponents(self, soup, containerTagName, componentName):
		"""
		@input: soup - soup object contains the DOM from scanning the source code
		@input: containerTagName - the container of soup object where the components are found  
		@input: componentname - the component name that this is searching 
		"""
		component_list = list()

		if soup.findAll(componentName):
			#If the XML is parsed nicely, findAll method will return all commandbuttons inside 
			#the <af:dialog> tags
			component_list = soup.findAll(componentName)
		elif soup.findNext():
			#Otherwise, the program will walk from one tag to another to search for
			#all the commandbuttons.  There are cases with more than two commandbuttons
			#If no commandbutton is found under dialog, skip to the next <af:dialog> tag 
			try:
				component = soup.findNext()
				while True:
					if component.findNext().name == containerTagName:
						break
					elif component.findNext().name == componentName:
						component_list.append(component.findNext())
					component = component.findNext()
			except:
				pass

		#A list of component instances
		components = list()
		#Add component to a Tag Instance		
		if component_list:					
			for component in component_list:
				print "name:", component.name
				try:								
					newComponent = Component()
					newComponent.tagName = component.name
					newComponent.soup = component	
					newComponent.sourceAttrs = component.attrs

					#Tag Component's attributes
					if newComponent.sourceAttrs:					

						#Attributes Provided																		
						for key, value in newComponent.sourceAttrs:
							try:							
								if value != '':
									newComponent.attrs[(key)] = self.extractTitle(value)	
								else:
									newComponent.attrs[(key)] = None
							except:
								print "attribute value extraction error"		
								newComponent.attrs[(key)] = None	

					try:							
						if component['id']:
							newComponent.id = component['id']
					except:
						print "no component id"						
					
					#Add found component to the list
					components.append(newComponent)								
				except:
					"cannot process found components"
					pass			
		else:
			print (componentName, " is not found")
						 
		if components:
			return components
		else:
			print "no components found with name: ", componentName
			return False

	def searchDialogs(self):
		dialogs = list()

		dialog_list = self.resultSoup.findAll('af:dialog')
		if dialog_list:
			for dialog in dialog_list:
				try:
					if dialog:
						modal = None
						try:
							if dialog['modal']:
								modal = dialog['modal']
						except:
							print "no modal"

						newDialog = Dialog(dialog['title'], dialog['id'], modal)	
						newDialog.soup = dialog		
						try:
							if dialog.parent:
								newDialog.parentNames.append(dialog.parent.name)
							if dialog.parent.parent:
								newDialog.parentNames.append(dialog.parent.parent.name)
						except:
							print "parent no found"

						dialogs.append(newDialog)	
					else:
						print ("There is no dialog found")
						pass 
				except:
					pass	
		if dialogs:
			return dialogs
		else:
			return False

	def searchTags(self, tagName=None, tagAttrs=None):
		tags = list()

		if tagName is not None and tagAttrs is not None:
			print "all attr:", tagAttrs, " name:", tagName
			tag_list = self.resultSoup.findAll(tagName, attrs=tagAttrs)
		elif tagName is not None:
			print "tagname:", tagName
			tag_list = self.resultSoup.findAll(tagName)
		elif tagAttrs is not None:
			print "attr:", tagAttrs
			tag_list = self.resultSoup.findAll(attrs=tagAttrs)
		else:
			print "all:"
			tag_list = self.resultSoup.findAll(True)

		if tag_list:
			print "number of tags:", len(tag_list)
			for tag in tag_list:
				try:								
					newTag = Tag()
					newTag.tagName = tag.name
					newTag.soup = tag	
					newTag.sourceAttrs = tag.attrs
					try:
						if tag.parent:
							newTag.parentNames.append(tag.parent.name)
						if tag.parent.parent:
							newTag.parentNames.append(tag.parent.parent.name)
					except:
						print "parent no found"

					try:							
						if tag['id']:
							newTag.id = tag['id']
					except:
						print "no tag id"						
					
					tags.append(newTag)						
				except:
					print "Tag object cannot be created"
					pass	
		else:
			print "no tag found"

		if tags:
			return tags
		else:
			print "no tags found with name: ", tagName
			return False

	def searchCSet(self):
		"""
		C:SET is a variable for bundle ID used throughout the JSF file
		"""
		cset_list = self.resultSoup.findAll('c:set')

		if cset_list:
			for cset in cset_list:
				var = cset['var']
				value = cset['value']

				print "var:", var, " value:", value	
				
				self.bundlePathDict[(var)] = value
		else:
			print "no cset found"

	def exploreSource(self):
		"""
		@Output: A Tuple with unique lists of Tag Names and Tag Attributes
		"""
		url = ''
		try:
			url = self.getTargetFullPath()
		except:
			print "No Download Link Provided"
			return False

		try:
			new_agent = HttpAgent(url)
			if new_agent:
				print "new agent created"
				response = new_agent.RequestResponse()
			else:
				print "no agent is established"
		except:
			print "Error: Cannot establish http agent"

		#From the source file, convert it to soup
		if response:
			selfClosingTags = ['c:set', 'f:facet', 'af:popup', 'af:panelGroupLayout', 'af:spacer', 'af:panelHeader']

			another_soup = None
			try:
				another_soup = Soup.HTMLToStoneSoup(response, selfClosingTags)
				self.resultSoup = another_soup

				attrSet = Set()
				tagSet = Set()

				allTags = self.resultSoup.findAll(True)
				for tag in allTags:
					tagSet.add(tag.name)
					for attr in tag.attrs:
						attrSet.add(attr[0])

				return (tagSet, attrSet)
			except:
				print "Error: Cannot convert http response into soup"
		else:
			print "no soup"
			pass

	def searchSource(self):
		url = ''
		try:
			url = self.getTargetFullPath()
		except:
			print "No Download Link Provided"
			return False

		try:
			new_agent = HttpAgent(url)
			if new_agent:
				print "new agent created"
				response = new_agent.RequestResponse()
			else:
				print "no agent is established"
		except:
			print "Error: Cannot establish http agent"

		#From the source file, convert it to soup
		if response:
			selfClosingTags = ['c:set', 'f:facet', 'af:popup', 'af:panelGroupLayout', 'af:spacer', 'af:panelHeader']

			another_soup = None
			try:
				another_soup = Soup.HTMLToStoneSoup(response, selfClosingTags)
				self.resultSoup = another_soup
			except:
				print "Error: Cannot convert http response into soup"

			#Search for all C:SET tags
			#C:SET Tags are hashkeys to the resource bundles
			self.searchCSet()

		else:
			print "no soup"
			pass

	def printDialogs(self, dialog_list=None, fh=None, bfh=None):
		if dialog_list is None or fh is None:
			return
		#Folder Hierarchy starting from Oracle/App
		folderStruc = self.getFolderStructure()

		#Output File Header	
		dialog_counter = 0
		for dialog in dialog_list:
			print "dialog ", dialog_counter
			dialog_counter += 1
			dialogOutputLn = ''

			outputLn = (self.target, folderStruc, dialog_counter, dialog.source, dialog.id, dialog.modal)
			

			#Inspect the command buttons within a dialog
			dialog.cancelButtonPair()
			#Create the output for the command button stats 
			dialogOutputLn = dialog.printButtonPair() + '\t' + dialog.printStats()	
			
			#print >>fh, '\t'.join([str(x) for x in outputLn]) + '\t' + '>'.join(dialog.parentNames[::-1]) + '\t' + dialogOutputLn		
			if len(dialog.commandButton_list) > 0 or len(dialog.component_list) > 0:
				print "dialog has button or components"
				if dialog.commandButton_list:				
					for component in dialog.commandButton_list:
						attrsOutputLn = 'af:commandbutton'
						if component.attrs:
							attr_dict = component.attrs
							for k,v in attr_dict.items():
								attrsOutputLn += '\t' + str(k) + ":" + re.sub(r'[\t\n]+', ' ', str(v))

						print >>fh, '\t'.join([str(x) for x in outputLn]) + '\t' + '>'.join(dialog.parentNames[::-1]) + '\t' + dialogOutputLn + '\t' + attrsOutputLn			

				if dialog.component_list:
					for component in dialog.component_list:
						attrsOutputLn = component.tagName
						if component.attrs:
							attr_dict = component.attrs
							for k,v in attr_dict.items():
								attrsOutputLn += '\t' + str(k) + ":" + re.sub(r'[\t\n]+', ' ', str(v))

						print >>fh, '\t'.join([str(x) for x in outputLn]) + '\t' + '>'.join(dialog.parentNames[::-1]) + '\t' + dialogOutputLn + '\t' + attrsOutputLn
			else:
				print >>fh, '\t'.join([str(x) for x in outputLn]) + '\t' + '>'.join(dialog.parentNames[::-1]) + '\t' + dialogOutputLn + '\t' + attrsOutputLn

	def printTags(self, tag_list=None, fh=None, bfh=None):
		if tag_list is None or fh is None:
			return

		folderStruc = self.getFolderStructure() #get the folder level names starting from oracle/app

		tag_counter = 0
		for tag in tag_list:
			tag_counter += 1

			attrsOutputLn = ''
			if tag.attrs:
				attr_dict = tag.attrs
				for k,v in attr_dict.items():
					attrsOutputLn += '\t' + str(k) + ":" + re.sub(r'[\t\n]+', ' ', str(v))			

			outputLn = (self.target, folderStruc, tag_counter, tag.tagName)

			print >>fh, '\t'.join([str(x) for x in outputLn]) + '\t' + '>'.join(tag.parentNames[::-1]) + attrsOutputLn

	def printTagImages(self, tag_list=None, fh=None, bfh=None):
		if tag_list is None or fh is None:
			return

		folderStruc = self.getFolderStructure()

		tag_counter = 0
		for tag in tag_list:
			tag_counter += 1

			outputLn = (self.target, folderStruc, tag_counter, tag.tagName)

			image_counter = 0
			for attrName, imagePath in tag.image_list:
				image_counter += 1

				#Split FileExtension
				fileName, fileExtension = os.path.splitext(imagePath)

				#Remove \r or \n newline space for Excel CSV formatting
				attrValue =  re.sub(r'[\t\n]+', ' ', str(tag.attrs[(attrName)]))  #original attribute value 				

				print >>fh, '\t'.join([str(x) for x in outputLn]) + '\t' + '>'.join(tag.parentNames[::-1]) + '\t' + attrName + '\t' + fileExtension + '\t' + imagePath	+ '\t' + attrValue			