import requests as req
from logging_manager import vanalytics_api_logger
from waitress import serve
# import logging
# import logers
import os
import json
from flask import Flask, jsonify, request
from flask_api import status
import vanalytics_data as v_data

# vanalytics_api_logger.basicConfig(filename='vanalytics_vanalytics_api_logger.log', filemode='w', format='%(name)s - %(levelname)s - %(asctime)s - %(message)s')
# log = logers.customLogger(logging.DEBUG)

DIR = os.path.dirname(__file__)
if not DIR:
    FILE_PATH = "main_config.json"
else:
    FILE_PATH = DIR + "/main_config.json"


with open(FILE_PATH, 'r') as readfile:
    main_config = json.load(readfile)

app = Flask(__name__)

#   hosted api's START
@app.route("/ping", methods=["GET"])
def ping():
    content = {"status": "service is alive"}
    return content, status.HTTP_200_OK

@app.route("/addupdateequipment", methods=["POST"])
def addupdateequipment():
    equipment_list = []
    try:
        equipment_list = request.get_json(force=True)
        if len(equipment_list) == 0:
            content = {"status": "invalid data received"}
            return content, status.HTTP_400_BAD_REQUEST
    except Exception as ex:
        vanalytics_api_logger.error(f"Bad input received {equipment_list}", exc_info=True)
        content = {"status": "invalid data received"}
        return content, status.HTTP_400_BAD_REQUEST
    
    try:
        v_data.CommonFeatures.updateEquipment(equipment_list)
        #v_data.CommonFeatures.update_equipment_process(equipment_list)
        content = {"status": "ok"}
        return content, status.HTTP_200_OK
    except Exception as ex2:
        vanalytics_api_logger.error(f"Failed to add following equipments: {equipment_list}", exc_info=True)
        content = {"status": "internal server error"}
        return content, status.HTTP_500_INTERNAL_SERVER_ERROR
#   hosted api's ENDS

def host_api():
    try:
        ip_address = main_config["initial_config"]["ip_address"]
        port_no = main_config["initial_config"]["port_number"]
        serve(app, host=ip_address, port=port_no)
        vanalytics_api_logger.info(f"Successfully hosted the api at given ip {ip_address} and port {port_no}")
    except Exception as ex:
        vanalytics_api_logger.error(f"Failed to host the api at given ip {ip_address} and port {port_no} with error {ex}", exc_info=True)
        print(f"Error in method: vanalytics_api.py - host_api, with ex {ex}")
    finally:
        pass