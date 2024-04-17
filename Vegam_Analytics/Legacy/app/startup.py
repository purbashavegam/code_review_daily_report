import requests as req
import json
import os


DIR = os.path.dirname(__file__)
if not DIR:
	FILE_PATH = "Config.json"
else:
	FILE_PATH = DIR + "/Config.json"


with open(FILE_PATH, 'r') as readfile:
	json_dict = json.load(readfile)

post_data_dict = {"UniqueName" : json_dict["posting_data"]["UniqueName"],
				  "UniqueId"   : json_dict["posting_data"]["UniqueId"],
				  "key"        : json_dict["posting_data"]["key"],
				  "tag"        : json_dict["posting_data"]["tag"],
				  "version"    : json_dict["posting_data"]["version"]}
# print(post_data_dict)

class Filter:
	def __init__(self, name="", id="", key=None, tag=None, version=0):
		self.UniqueName =  name
		self.UniqueId = id 
		self.key = key
		self.tag = tag
		self.version = 0
		self.json_dict = ""
		self.url= ""
		self.api_post_data = {}
		self.api_object = ""

	def getApiData(self):
		try:
			DIR = os.path.dirname(__file__)
			if not DIR:
				FILE_PATH = "Config.json"
			else:
				FILE_PATH = DIR + "/Config.json"
			self.filename = FILE_PATH
			with open(self.filename, 'r') as readfile:
				self.json_dict = json.load(readfile)
			self.api_post_data["UniqueName"] = self.UniqueName
			self.api_post_data["UniqueId"] = self.UniqueId
			self.api_post_data["key"] = self.key
			self.api_post_data["tag"] = self.tag
			self.api_post_data["version"] = self.version

			self.url = (self.json_dict['request_url'])
			self.api_object = json.loads((req.post(self.url, json = self.api_post_data)).text)
			return ((self.api_object))
		except Exception as e:
			print(str(e))


filter_obj = Filter(post_data_dict['UniqueName'],post_data_dict['UniqueId'],post_data_dict['key'],post_data_dict['tag'],post_data_dict['version'])
api_objectIs = (filter_obj.getApiData())
# print(api_objectIs)



class Entity:

	def __init__(self, main_api_object):
		self.api_post_data = main_api_object
		self.uniqueID = ""
		self.uniqueName = ""
		self.group = ""
		self.description = ""
		self.property = ""
		self.info = ""
		self.api_object = ""
		self.description = ""
		

	def details(self):
		try:
			self.api_object = self.api_post_data
			self.property = self.api_object["property"]
			return self.api_object
		except Exception as e:
			print(str(e))

	def apiInformations(self):
		try:
			self.uniqueID = self.api_object["uniqueID"]
			self.uniqueName = self.api_object["uniqueName"]
			self.group = self.api_object["group"]
			self.description = self.api_object["description"]
			self.info = self.api_object["info"]
			return self.uniqueID, self.uniqueName, self.group, self.description, self.info
		except Exception as e:
			print(str(e))

	def ProPerty(self):
		try:
			self.property = self.api_object["property"]
			return self.property
		except Exception as e:
			print(str(e))

	def CallerMain(self):
		try:
			self.details()
			self.apiInformations()
			self.ProPerty()
			
		except Exception as e:
			print(str(e))

mainobject = Entity(api_objectIs)
CallerAll = mainobject.CallerMain()


class Property(Entity):
	def __init__(self,propertyList,keyname,tagname):
		self.propertyObject = propertyList
		self.required_key = keyname
		self.required_tag = tagname
		self.key = ""
		self.value = ""
		self.dataType ="" 
		self.tag =""
		self.range ="" 
		self.unit =""
		self.description ="" 
		self.required_tag_list = []

	def propertyKeyMethod(self):
		try:
			for i in range(len(self.propertyObject)):
				if self.propertyObject[i]["key"] == self.required_key:
					return (self.propertyObject[i])
		except Exception as e:
			print(str(e))
			# self.key = self.property[i]["key"]
			# self.value = self.property[i]["value"]
			# self.dataType = self.property[i]["dataType"]
			# self.tag = self.property[i]["tag"]
			# self.range = self.property[i]["range"]
			# self.unit = self.property[i]["unit"]
			# self.description = self.property[i]["description"]
	def tagWiseInfo(self):
		# print(self.propertyObject)
		for i in range(len(self.propertyObject)):
			if self.required_tag in self.propertyObject[i]["tag"]:
				self.required_tag_list.append(self.propertyObject[i])
		return self.required_tag_list

		



property_lists = mainobject.ProPerty()

DriveEnd = Property(property_lists,"NumberOfBalls_DE","DriveEndBearing")
# ProPertyKeys =    (property_class.propertyKeyMethod())
propertyTags = DriveEnd.tagWiseInfo()
print('Drive end Bearing details',propertyTags)


NDE = Property(property_lists,"NumberOfBalls_DE","NonDriveEndBearing")
NDE_PropertyTags = NDE.tagWiseInfo()
print("Non drive end bearing details",NDE_PropertyTags)


































# class Property(Equipment):
# 	def __init__(self,):
# 		pass


# 	def propertyMethod(self):
# 		self.property = self.api_object["property"]
# 		print(self.property[Equipment.count]["key"])
# 		print(Equipment.count)
		# for i in range(len(self.property)):
		# 	print(i,len(self.property))
			# print(self.property[i]["value"])
		
		# print(self.property["key"])
		# self.key = self.property["key"]
		# self.value = self.property["value"]
		# self.dataType = self.property["dataType"]
		# self.tag = self.property["tag"]
		# self.range = self.property["range"]
		# self.unit = self.property["unit"]
		# self.description = self.property["description"]
		# return self.key,self.value,self.dataType,self.tag,self.range,self.unit,self.description





# myList = [1,2,3,4]

# class counter:
# 	count = 0
# 	def __init__(self,listis):
# 		self.mainlist = listis
# 		counter.count+=1

# 	def counteris(self):
# 		print(len(self.mainlist))
		

			


# obj = counter(myList)
# obj1 = counter(myList)
# obj2 = counter(myList)
# obj.counteris()
# print(counter.count)