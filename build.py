# Call imports
import os, zipfile, shutil, hashlib
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ElementTree
from hashlib import md5

# Constants
__currentDir__ = os.getcwd()
__include__ = ("plugin.video.", "repository.", "script.module.")
__exclude__ = (".pyo", ".pyc", "Thumbs.db", ".DS_Store")
__forceReplace__ = False

# Classes
class Generator(object):
	"""
		Generates a new addons.xml file from each addons addon.xml file
        and a new addons.xml.md5 hash file.
	"""
	def __init__(self):
		# Create paths to Resources
		self.master_xml = os.path.join(__currentDir__, "addons.xml")
		self.master_md5 = os.path.join(__currentDir__, "addons.xml.md5")
		self.temp_zip = os.path.join(__currentDir__, "temp.zip")
		self.addon_sources = os.path.dirname(__currentDir__)
		self.repo_dir = __currentDir__
		
		# Generate Repo
		self.generate_repo()
		
		# Generate xml
		self.generate_xml()
	
	def generate_repo(self):
		# Fetch list of Addons to add
		maxLength = 0
		availableAddons = []
		for addonDir in os.listdir(self.addon_sources):
			for include in __include__:
				if addonDir.startswith(include):
					availableAddons.append(addonDir)
					addonNameLength = len(addonDir)
					if addonNameLength > maxLength:
						maxLength = addonNameLength
		
		# Create main Elementree Element
		self.tree = ElementTree.Element("addons")
		
		# Loop each addon and Create element and transor content to repo
		for addonId in availableAddons:
			# Create paths
			addonPath = os.path.join(self.addon_sources, addonId)
			xmlPath = os.path.join(addonPath, "addon.xml")
			logPath = os.path.join(addonPath, "changelog.txt")
			fanartPath = os.path.join(addonPath, "fanart.jpg")
			iconPath = os.path.join(addonPath, "icon.png")
			
			# Parse addon.xml element
			addonElement = self.addonElement(xmlPath)
			self.tree.append(addonElement)
			version = self.fetchVersion(addonElement)
			
			addonDest = os.path.join(self.repo_dir, addonId)
			ZipDest = os.path.join(addonDest, "%s-%s.zip" % (addonId, version))
			logDest = os.path.join(addonDest, "changelog-%s.txt" % version)
			fanartDest = os.path.join(addonDest, "fanart.jpg")
			iconDest = os.path.join(addonDest, "icon.png")
			
			# Create addon directory if does not exist
			if not os.path.exists(addonDest): os.mkdir(addonDest)
			
			# Create Addon Zip
			try:
				print ("Creating Zipfie for %s" % addonId).ljust(23 + maxLength, "."),
				self.generater_zip(addonPath, ZipDest)
			except:
				print "Failed"
				if os.path.exists(self.temp_zip): os.remove(self.temp_zip)
			else:
				# Move required item to destination
				if self.check_diff(self.temp_zip, ZipDest):
					shutil.move(self.temp_zip, ZipDest)
					print "done"
				else:
					os.remove(self.temp_zip)
					print "Skipped"
				
				# Copy over extra files if available
				if os.path.isfile(logPath) and self.check_diff(logPath, logDest): shutil.copyfile(logPath, logDest)
				if os.path.isfile(iconPath) and self.check_diff(iconPath, iconDest): shutil.copyfile(iconPath, iconDest)
				if os.path.isfile(fanartPath) and self.check_diff(fanartPath, fanartDest): shutil.copyfile(fanartPath, fanartDest)
	
	def addonElement(self, xmlPath):
		# Parse xml and return root element
		tree = ElementTree.parse(xmlPath)
		return tree.getroot()
	
	def fetchVersion(self, element):
		# Fetch Version Attribute from element
		return element.get("version")
	
	def generater_zip(self, addonPath, zipPath):
		# Initialize zipping module
		zipObj = zipfile.ZipFile(self.temp_zip, "w", compression=zipfile.ZIP_DEFLATED)
		
		# Scan Directory to be ziped
		for dirpath, dirnames, filenames in os.walk(addonPath):
			# Skip directory if its the git cache
			if ".git" in dirpath: continue
			else:
				for filename in (fileName for fileName in filenames if self.check_exclude(fileName)):
					# Create Absolute and Relative Paths
					absolutePath = os.path.join(dirpath, filename)
					relativePath = absolutePath.replace(os.path.dirname(addonPath),"")
					# Add file to zipfile
					zipObj.write(absolutePath, relativePath, zipfile.ZIP_DEFLATED)
		
		# Close connection to zip file
		zipObj.close()
	
	def check_exclude(self, filename):
		for exclude in __exclude__:
			if filename.endswith(exclude):
				return False
		return True
	
	def check_diff(self, src, dst):
		# Check checksum of Source and Destination
		if not os.path.exists(dst) or __forceReplace__: return True
		else:
			srcHash = self.checksum(self.read_file(src))
			dstHash = self.checksum(self.read_file(dst))
			return srcHash != dstHash
	
	def generate_xml(self):
		# Save out addons.xml
		rough_string = ElementTree.tostring(self.tree, "utf-8").replace("\n","").replace("\t","")
		reparsed = minidom.parseString(rough_string)
		newXmlData = reparsed.toprettyxml(indent="\t", encoding="utf8")
		self.write_file(self.master_xml, newXmlData)
		
		# Read back file and Calculate MD5
		xmlData = self.read_file(self.master_xml)
		hash = self.checksum(xmlData)
		
		# Save Hash to file
		self.write_file(self.master_md5, hash)
	
	def checksum(self, data):
		return md5(data).hexdigest()
	
	def read_file(self, filename):
		with open(filename, "rb") as openedfile:
			return openedfile.read()
	
	def write_file(self, filename, filedata):
		with open(filename, "wb") as openedfile:
			openedfile.write(filedata)

Generator()