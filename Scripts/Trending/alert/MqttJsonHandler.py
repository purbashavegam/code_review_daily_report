"""
This module implemets general functionalilities related
to json file
"""
import json
import os


class AnalyticsJsonHandler:
    """
    This is a class for implemeting general functionalities of json file

    Attributes:
        filename(string): filename of json file
        json_dict(dict) : dictionary that stores content of json file
    """
    def __init__(self, file_name):

        self.filename = file_name
        self.json_dict = self.read_json()
        # self.key_trends = trends_key
        # print(self.key_trends)

    def read_json(self):
        """
        This method is to read the json file

        Returns:
            json_dict(dict): dictionary that store json file content

        """
        try:
            with open(self.filename, 'r') as readfile:
                self.json_dict = json.load(readfile)
            return self.json_dict
        except ValueError as error:
            raise ValueError("Json file is empty") from error

    def update_json(self):
        """
        This method is to update the json file
        """
        if self.json_dict:
            with open(".filepath.json.tmp", "w") as writefile:
                json.dump(self.json_dict, writefile, indent=4)
            os.replace(".filepath.json.tmp", self.filename)
        else:
            raise ValueError("JSON file is empty")

    def get_all_settings(self):
        """
        This method is to get all the properties from the json file
        Returns:
            key_valueType_list(list): List of tuples each having property
                                      and type of value of that property

        """
        key_valuetype_list = []
        if self.json_dict:
            for prop in self.json_dict:
                key_valuetype_tuple = (prop, type(self.json_dict[prop]))
                key_valuetype_list.append(key_valuetype_tuple)
        else:
            raise ValueError("JSON file is empty")
        return key_valuetype_list

    def change_property(self, json_property, new_value):
        """
        This method is to change the value of any property in json file

        Args:
            json_property(string): Property to be changed
            new_value: New value of the property

        """
        self.json_dict = self.read_json()
        if self.json_dict:
            temp_dictionary = self.json_dict
            property_list = json_property.split(".")
            for key in property_list[:-1]:
                temp_dictionary = temp_dictionary[key]
            temp_dictionary[property_list[-1]] = new_value
            self.update_json()

    def get_property(self, json_property):
        temp_dictionary = {} #pm
        property_list = [] #pm
        """
        This method is to get the value of any property from the json file

        Args:
            json_property(string): Property whose value to be returned
        Returns:
            value: Value of the property passed as argument
        """
        self.json_dict = self.read_json()["Mqtt"]#self.read_json()[self.key_trends]#["Mqtt"]
        print(self.json_dict,"----------")
        if self.json_dict:
            temp_dictionary = self.json_dict
            property_list = json_property.split(".")
            for key in property_list[:-1]:
                temp_dictionary = temp_dictionary[key]
        return temp_dictionary[property_list[-1]]




