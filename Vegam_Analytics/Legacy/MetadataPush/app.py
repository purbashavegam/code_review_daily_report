import logging
import logger as app_log
from util import Utility
import json
import os
import requests as httpReq

log = app_log.app_logger(logging.DEBUG)
dir = os.path.dirname(__file__)
file_path = None
if not dir:
    file_path = "app_config.json"
else:
    file_path = dir + "/app_config.json"

log.info("Start of App..")

def read_config_file():    
    with open(file_path, "r") as read_file:
        Utility.app_config = json.load(read_file)

def read_uploaded_file(fileName):
    new_file_path = dir + "/datafile/" + fileName
    try:
        Utility.metadata_obj = {}
        with open(new_file_path, "r") as read_file:
            Utility.metadata_obj = json.load(read_file)
            print(f"File read successfully")
            return 0
    except Exception as ex:
        print(f"ERROR: {ex}, check log for more information")
        log.error(f"Error while reading the file: {fileName}", exc_info=True)

def check_filedata():
    try:
        token = Utility.metadata_obj["token"]
        token = token.strip()
        if len(token) < 1:
            print("Token is missing...")
            return
        data = Utility.metadata_obj["data"]
        if len(data) < 1:
            print("Data is missing")
            return
        
        print(f"Number of items to process: {len(data)}")
        process_data(token, data)
    except Exception as ex:
        print(f"ERROR: {ex}, check log for more information")
        log.error(f"Error parsing data", exc_info=True)

def process_data(token, data):
    if len(data) > 0:
        try:
            d = data.pop(0)
            print(f"Processing for uniquename: {d['uniquename']}")
            print(f"checking if record already exist...")
            
            url = Utility.app_config["metadata_api_info"]["base_url"] + "getmetadata?token=" + token
            post_data = {
                "UniqueName" : d["uniquename"]
                , "UniqueId" : ""
                , "Key": []
                , "Tag": []
            }

            response = httpReq.post(url, json=post_data, headers={"Content-Type":"application/json"})
            if response is not None:
                if response.status_code == 200:
                    metadata_obj = prepare_data(d)
                    if response.text == 'null':
                        print(f"Record does not exist with name {d['uniquename']}, Creating new entry")
                        url = Utility.app_config["metadata_api_info"]["base_url"] + "addmetadata?token=" + token                        
                    else:
                        print(f"Record exist, adding provided keys")
                        text_json = json.loads(response.text)
                        metadata_obj["uniqueID"] = text_json["uniqueID"]
                        url = Utility.app_config["metadata_api_info"]["base_url"] + "addmetadatakey?token=" + token

                    response = httpReq.post(url, json=metadata_obj, headers={"Content-Type":"application/json"})

                    if response.status_code == 200:
                        if response.text != 'null':
                            text_json = json.loads(response.text)
                            print(f"Data updated successfully: {text_json}")
                        else:
                            print("No response from metadata api, try again")
                    else:
                        print(f"Unable to process with Code: {response.status_code}, Text: {response.text}")
                        log.info(f"Unable to process with Code: {response.status_code}, Text: {response.text}")
                else:
                    print(f"Unable to process with Code: {response.status_code}, Text: {response.text}")
                    log.info(f"Unable to process with Code: {response.status_code}, Text: {response.text}")
            else:
                print(f"No respose received from metadata api, try after some time")
                log.info(f"No respose received from metadata api, try after some time")
            
            print("\n")
        except Exception as ex:
            print(f"ERROR: failed to add metadata for data: {data} with error {ex}")
            log.error(f"ERROR: failed to add metadata for data: {data}", exc_info=True)
        finally:
            process_data(token, data)

def prepare_data(d):
    if "property" in d.keys():
        property_info = d["property"]
        if "key" in property_info and "value" in property_info:
            keys = property_info["key"]
            values = property_info["value"]
            if len(keys) > 0 and len(keys) == len(values):
                properties = []
                for k in range(len(keys)):
                    prop = {
                        "key": keys[k]
                        , "value": values[k]
                        , "dataType": ""
                        , "tag": []
                        , "range": []
                        , "unit": ""
                        , "description": ""
                    }
                    properties.append(prop)
                
                metadata_obj = {
                    "uniqueID": ""
                    , "uniqueName": d['uniquename']
                    , "group": ""
                    , "description": ""
                    , "property": properties
                }

                return metadata_obj
            else:
                print("mismatch between provided key and value, cannot process")
                return None
        else:
            print("key/value missing in the given json file, cannot process")
            return None
    else:
        print("property is missing in the given json file, cannot process")
        return None

read_config_file()

while True:
    user_input = input("Please provide the file name:\t")
    fileName = user_input.strip()
    if len(fileName) > 0:
        output = read_uploaded_file(fileName)
        if output == 0:
            check_filedata()
    else:
        print("Invalid input")
    
    print("\n")