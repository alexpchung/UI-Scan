import re
from sets import Set

class CommandButton(object):
	"""CommandButton"""
	def __init__(self, textAndAccessKey=None, commandButtonID=None, shortDesc=None):
		self.textAndAccessKey = textAndAccessKey
		self.commandButtonID = commandButtonID
		self.shortDesc = shortDesc

class Component(object):
	"""Sub component embedded within a tag"""
	def __init__(self):
		self.tagName = None
		self.name = None
		self.sourceAttrs = None
		self.attrs = dict()
		self.soup = None
		self.id = None
		self.title = None
		self.shortDesc = None

class Tag(object):
	"""Generic Tag"""
	def __init__(self):
		self.tagName = None
		self.name = None
		self.title = None
		self.id = None
		self.sourceAttrs = None
		self.attrs = dict()
		self.soup = None
		self.image_list = list()
		self.bundleURL_list = Set()
		self.parentNames = list()
		self.component_list = list()
		self.shortDesc = None

	def initItems(self, tagName=None, title=None, id=None):
		self.tagName = tagName
		self.title = title
		self.id = id

	def addComponent(self, component):
		self.component_list.append(component)

class Dialog(Tag):
	"""Contextual Dialog"""
	def __init__(self, title=None, dialogID=None, modal=None):
		super(Dialog, self).__init__()
		self.initItems('dialog', title, dialogID)
		self.modal = modal

		self.source = None
		self.notes = None

		self.commandButton_list = list()

		self.hasCancel = 0
		self.hasOK = 0
		self.hasDONE = 0
		self.hasSaveAndClose = 0
		
	def addCommandButton(self, commandbutton):
		self.commandButton_list.append(commandbutton)

	def cancelButtonPair(self):		
		for button in self.commandButton_list:
			#Check for button label with string "CANCEL"

			buttonAttr_dict = button.attrs
			if re.search('CANCEL', buttonAttr_dict['textandaccesskey'], re.I):
				self.hasCancel = 1
			elif re.search('OK', buttonAttr_dict['textandaccesskey'], re.I):
				self.hasOK = 1
			elif re.search('DONE', buttonAttr_dict['textandaccesskey'], re.I):
				self.hasDONE = 1
			elif re.search('SAVE_AND_CLOSE', buttonAttr_dict['textandaccesskey'], re.I):
				self.hasSaveAndClose = 1
			else:
				pass

	def printButtonPair(self):
		if self.hasCancel == 1 and self.hasDONE == 1:
			return "Cancel and Done"
		elif self.hasCancel == 1 and self.hasOK == 1:
			return "OK and Cancel"
		elif self.hasCancel == 1 and self.hasSaveAndClose == 1:
			return "Save and Close and Cancel"
		else:
			return "Others"

	def printStats(self):
		output = str(len(self.commandButton_list)) + '\t' + str(self.hasCancel) + '\t' + str(self.hasOK) + '\t' + str(self.hasDONE) + '\t' + str(self.hasSaveAndClose)
		return output