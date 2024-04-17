import os
import logging
from types import SimpleNamespace
import json
import requests as req
import vanalytics_helper as v_helper
import mqtt_con as m_con
from enum import Enum
import numpy as np
import time
from logging_manager import vanalytics_data_logger
from util import ParserFftCalculation as fft_cal
import rpm as op_rpm
import gear.gear as algo_gearbox
import bearing.bearing as algo_bearing
import velocity_severity.machine_condition as algo_severity
import misalignment.misalignment as algo_misalignment
import looseness.looseness as algo_looseness
import machine_status.on_off as algo_onoff
import unbalance.unbalance as algo_unbalance
# log = logers.customLogger(logging.DEBUG)

DIR = os.path.dirname(__file__)
if not DIR:
    FILE_PATH = "main_config.json"
else:
    FILE_PATH = DIR + "/main_config.json"

with open(FILE_PATH, 'r') as readfile:
    main_config = json.load(readfile)

class VegamAlogrithm(Enum):
    VelocitySeverity = 1
    BearingFault = 2
    MisalignmentFault = 3
    UnbalanceFault = 4
    MechanicalLooseness = 5
    GearboxFault = 6
    MachineOnOff = 7

class CommonFeatures:
    #   will have site id list, used to get the equipment from the api for each site
    site_ids = []   
    #   if not able to get euipment, will store those site id here
    site_id_failed = [] 
    #   store the brokers and there respective client { key :- ipaddress_portnumber }
    brokers_dict = {}   

    #   will store id's for which metadata needs to be fetched { 'E': equipment_id & 'M': sensor_id}
    metadata_lookup = []    
    #   if not able to fetch metadata, id's will be stored here
    metadata_lookup_failed = [] 

    #   will store all the topics { 'topic_id': {'E': equipment_id, 'S': sensor_id, 'T': TagType}}
    topics_lookup = {}  
    #   will store the equipment data { equipment_id: {'E': equipment_data, 'M': equipment_metadata }}
    equipment_store = {}
    #   will store the sensor metadata {sensor_id: {'M': sensor_metadata}}    
    sensor_store = {}
    main_config = {}
    simulator_rpm = 0

    sensordata_lookup = {}

    cleanup_objects = []

    updated_equipments = {
        VegamAlogrithm.VelocitySeverity: [],
        VegamAlogrithm.MisalignmentFault: [],
        VegamAlogrithm.UnbalanceFault: [],
        VegamAlogrithm.BearingFault: [],
        VegamAlogrithm.GearboxFault: [],
        VegamAlogrithm.MechanicalLooseness: [],
        VegamAlogrithm.MachineOnOff: []
    }

    @classmethod
    def get_site_to_moniter(cls):
        queryStr = "?ipAddress=" + main_config["initial_config"]["ip_address"]
        queryStr = queryStr + "&portNumber=" + str(main_config["initial_config"]["port_number"])
        
        url = main_config["vmaint_api"]["base_url"]
        url = url + "/GetSitesToProcess" + queryStr
        print(url, "<--------------------------url ") #pm

        initial_data = None
        try:
            initial_data = req.post(url)
            if initial_data is not None:
                if initial_data.status_code == 200 and initial_data.text != 'null':
                    vanalytics_data_logger.info(initial_data.text)
                    return json.loads(initial_data.text)
            return []
        except Exception as ex:
            vanalytics_data_logger.error(f'Unable to get the initial list of sites from vmaint api with error: {ex}', exc_info=True)
    
    @classmethod
    def get_sites_equipments(cls):
        if len(CommonFeatures.site_ids) > 0:
            site_id = CommonFeatures.site_ids.pop()
            CommonFeatures.get_equipment_data(site_id)

    @classmethod
    def get_equipment_data(cls, site_id):
        '''
        @param site_id : site_id for which equipment data is required
        '''
        queryStr = "?ipAddress=" + main_config["initial_config"]["ip_address"]
        queryStr = queryStr + "&portNumber=" + str(main_config["initial_config"]["port_number"])
        queryStr = queryStr + "&siteID=" + str(site_id)

        url = main_config["vmaint_api"]["base_url"]
        url = url + "/GetAnalyticsEquipments" + queryStr

        equipment_data = None
        try:
            equipment_data = req.post(url)
            if equipment_data is not None:
                if equipment_data.status_code == 200 and equipment_data.text != 'null':
                    equipment_list = json.loads(equipment_data.text)
                    CommonFeatures.store_equipment_data(equipment_list)
                else:
                    CommonFeatures.site_id_failed.append(site_id)
            else:
                CommonFeatures.site_id_failed.append(site_id)
        except Exception as ex:
            vanalytics_data_logger.error(f'Unable to get the equiment data from vmaint for the site id:- {site_id} with error {ex}', exc_info=True)
            CommonFeatures.site_id_failed.append(site_id)
        finally:
            CommonFeatures.get_sites_equipments()

    @classmethod
    def store_equipment_data(cls, equipment_list):
        '''
        @param equipment_list : list of equipments to be stored
        '''
        skip_list = main_config["skip_list"]["sensor_ids"]
        for equipment in equipment_list:
            equipment_obj = json.loads(json.dumps(equipment), object_hook=lambda d: SimpleNamespace(**d))                
            if len(equipment_obj.Brokers) == 0:
                continue
            CommonFeatures.equipment_store[equipment_obj.EquipmentID] = {'E' : equipment_obj, 'M' : None }
            CommonFeatures.metadata_lookup.append({ 'E' : equipment_obj.EquipmentID })
            temp = equipment_obj.Brokers[0]
            broker_key = temp.IpAddress + "_" + str(temp.PortNumber)
            if broker_key not in CommonFeatures.brokers_dict:
                broker = v_helper.BrokerInfo(temp.IpAddress, temp.PortNumber, temp.UserName, temp.Password)
                CommonFeatures.brokers_dict[broker_key] = broker
            if len(equipment_obj.AttachedSensors) > 0:
                for sensor in equipment_obj.AttachedSensors:
                    if sensor.SensorMacID in skip_list:
                        continue
                    CommonFeatures.metadata_lookup.append({ 'S' : sensor.SensorMacID })
                    if (sensor.SensorMacID in CommonFeatures.sensor_store.keys()) == False:
                        CommonFeatures.sensor_store[sensor.SensorMacID] = None
                    #data=CommonFeatures.sensor_store.values()
                    """if  (sensor.AxisX in data) == 'AXIAL':
                        print("yes")
                    if  (sensor.AxisX in data) == 'HORIZONTAL_R':
                        print("NO")
                    if  (sensor.AxisX in data) == 'VERTICAL_R':
                        print("NOOO")"""
                    if len(sensor.Tags) > 0:
                        for tag in sensor.Tags:
                            CommonFeatures.topics_lookup[tag.Topic] = { 'E' : equipment_obj.EquipmentID, 'S': sensor.SensorMacID, 'T': tag.TopicRepresents }
                            if tag.TopicType == "S":
                                CommonFeatures.brokers_dict[broker_key].SubTopics.append(tag.Topic)
                            
                        CommonFeatures.brokers_dict[broker_key].SubTopics = list(set(CommonFeatures.brokers_dict[broker_key].SubTopics))

    @classmethod
    def get_metadata(cls):
        if len(CommonFeatures.metadata_lookup) > 0:
            metadata_item = CommonFeatures.metadata_lookup.pop()
            CommonFeatures.call_metadata_api(metadata_item)

    @classmethod
    def call_metadata_api(cls, metadata_item):
        id = ""
        mtype = "E"
        if 'E' in metadata_item:
            id = metadata_item['E']
        else:
            id = metadata_item['S']
            mtype = "S"
        
        post_data = {
            "UniqueName" : id
            , "UniqueId" : ""
            , "Key": []
            , "Tag": []
        }

        url = main_config["metadata_api_info"]["base_url"]

        try:            
            metadata = req.post(url, json=post_data, headers={"Content-Type":"application/json"})
            if metadata is not None:
                if(metadata.status_code == 200 and metadata.text != 'null'):
                    metadata = json.loads(metadata.text)
                    CommonFeatures.store_metadata(metadata, metadata_item, mtype)
                else:
                    CommonFeatures.store_metadata(None, metadata_item, mtype)
                    CommonFeatures.metadata_lookup_failed.append(metadata_item)
            else:                
                CommonFeatures.store_metadata(None, metadata_item, mtype)
                CommonFeatures.metadata_lookup_failed.append(metadata_item)
        except Exception as ex:
            vanalytics_data_logger.error(f'Unable to get the equiment/sensor data from metadata for the unique_name:- {id} with error: {ex}', exc_info=True)
            CommonFeatures.metadata_lookup_failed.append(metadata_item)
        finally:
            CommonFeatures.get_metadata()

    @classmethod
    def store_metadata(cls, metadata, metadata_item, mtype):
        try:
            if metadata is None:
                if mtype == 'M':
                    CommonFeatures.sensor_store[metadata_item['S']] = { 'M' : None, 'H' : None }

            metadata_obj = json.loads(json.dumps(metadata), object_hook=lambda d: SimpleNamespace(**d))
            if mtype == 'E':
                CommonFeatures.equipment_store[metadata_item['E']]['M'] = metadata_obj
            else:
                CommonFeatures.sensor_store[metadata_item['S']] = { 'M' : metadata_obj, 'H' : None }
        except Exception as ex:
            vanalytics_data_logger.error(f'Unable to store data {metadata} with error: {ex}', exc_info=True)

    @classmethod
    def connect_subscribe_mqtt(cls, broker_keys):
        '''
        @param broker_key : list of broker key [key: ipaddress + '_' + port] 
        '''
        if len(broker_keys) > 0:
            broker_key = broker_keys.pop()
            try:
                broker_info = CommonFeatures.brokers_dict[broker_key]
                if broker_info.MqttClient is not None and broker_info.MqttClient.isConnected == 1:
                    pass
                else:
                    broker_info.MqttClient = m_con.MqttClient(broker_info.ipAddress, broker_info.portNumber, broker_info.userName, broker_info.password, broker_info.brokerName)
                    broker_info.MqttClient.connect_broker()

                sub_topics = broker_info.SubTopics[:]
                sub_topics.append("se_poc/rpm")
                # broker_info.SubTopics = []
                broker_info.MqttClient.subscribe_topic(sub_topics)                
            except Exception as ex:
                vanalytics_data_logger.error(f'Failed to connect/subscribe {broker_key} with error: {ex}', exc_info=True)
            finally:
                CommonFeatures.connect_subscribe_mqtt(broker_keys)

    @classmethod
    def updateEquipment(cls, equipments):
        CommonFeatures.store_equipment_data(equipments)

        if len(CommonFeatures.metadata_lookup) > 0:
            CommonFeatures.get_metadata()

        broker_keys = list(CommonFeatures.brokers_dict.keys())
        if len(broker_keys) > 0:
            CommonFeatures.connect_subscribe_mqtt(broker_keys)

    @classmethod
    def update_equipment_process(cls, equipments):
        for equipment in equipments:
            equipment_obj = json.loads(json.dumps(equipment), object_hook=lambda d: SimpleNamespace(**d))
            CommonFeatures.updated_equipments[VegamAlogrithm.VelocitySeverity].append(equipment_obj.EquipmentID)
            CommonFeatures.updated_equipments[VegamAlogrithm.MisalignmentFault].append(equipment_obj.EquipmentID)
            CommonFeatures.updated_equipments[VegamAlogrithm.UnbalanceFault].append(equipment_obj.EquipmentID)
            CommonFeatures.updated_equipments[VegamAlogrithm.BearingFault].append(equipment_obj.EquipmentID)
            CommonFeatures.updated_equipments[VegamAlogrithm.GearboxFault].append(equipment_obj.EquipmentID)
            CommonFeatures.updated_equipments[VegamAlogrithm.MechanicalLooseness].append(equipment_obj.EquipmentID)
            CommonFeatures.updated_equipments[VegamAlogrithm.MachineOnOff].append(equipment_obj.EquipmentID)

    @classmethod
    def getSensorMetadata(cls, sensor_id, args):
        '''
        @param sensor_id : sensor id for which metadata needs to be searched
        @args : list of metadata keys e.g.['power', 'modelnumber']
        @return : it will return list, [['256'], ['vsens_234']]
        '''
        output = []
        try:
            if sensor_id in CommonFeatures.sensor_store:
                if CommonFeatures.sensor_store[sensor_id] is not None:
                    if CommonFeatures.sensor_store[sensor_id]['M'] is not None:
                        metadata_prop = CommonFeatures.sensor_store[sensor_id]['M'].property
                        for t in args:
                            data = next(
                                (x for x in metadata_prop if x.key.lower() == t.lower()), None)
                            if data is not None:
                                output.append(data.value)
                            else:
                                output.append(None)
        except Exception as ex:
            vanalytics_data_logger.error(
                f"failed to get sensor metadata for the list {args}", exc_info=True)
        finally:
            # TODO need to remove after all data is validated
            return output

    @classmethod
    def getEquipmentData(cls, equipment_id, sensor_id, args):
        '''
        @param equipment_id : equipment id for which data requied
        @param sensor_id : sensor id for which data needs to be searched
        @args : current version supports following keys ['axisx', 'axisy', 'axisz', 'connectionmode']
        @return : it will return list, ['x', 'y', 'z', 'B']
        '''
        output = []
        try:
            if equipment_id in CommonFeatures.equipment_store:
                equipment = CommonFeatures.equipment_store[equipment_id]['E']
                sensors = equipment.AttachedSensors
                 
                req_sensor = next(
                    (x for x in sensors if x.SensorMacID == sensor_id), None)
            
                if req_sensor is not None:
                    for y in args:
                        y = y.lower()
                        if y == 'axisx':
                            output.append(req_sensor.AxisX)
                        elif y == "axisy":
                            output.append(req_sensor.AxisY)
                        elif y == "axisz":
                            output.append(req_sensor.AxisZ)
                        elif y == "connectionmode":
                            output.append(req_sensor.ConnectionMode)
                        else:
                            output.append(None)
        except Exception as ex:
            print(f"Error in method: vanalytics_data.py - getEquipmentData, with ex: {ex}")
            #   write log here
        finally:
            # TODO need to remove after all data is validated
            return output

    @classmethod
    def getEquipmentMetaData(cls, equipment_id, args):
        '''
        @param equipment_id : equipment id for which metada requied
        @param sensor_id : sensor id for which metadata needs to be searched
        @args : list of metadata keys e.g.['power', 'modelnumber']
        @return : it will return list, [['256'], ['vsens_234']]
        '''
        output = []
        try:
            if equipment_id in CommonFeatures.equipment_store:
                data = CommonFeatures.equipment_store[equipment_id]['M']
                if data is not None:
                    metadata_prop = data.property
                    for t in args:
                        data = next(
                            (x for x in metadata_prop if x.key.lower() == t.lower()), None)
                        if data is not None:
                            output.append(data.value)
                        else:
                            output.append(None)
        except Exception as ex:
            vanalytics_data_logger.error(
                f"failed to get equipment metadata for the list {args}", exc_info=True)
        finally:
            # TODO need to remove after all data is validated
            return output

    @classmethod
    def getAxisInfo(cls, equipment_id, sensor_id, args):
        output = []
        try:
            if equipment_id in CommonFeatures.equipment_store:
                equipment = CommonFeatures.equipment_store[equipment_id]['E']
                sensors = equipment.AttachedSensors
                req_sensor = next(
                    (x for x in sensors if x.SensorMacID == sensor_id), None)
               
                for y in args:
                        y = y.lower()
                        if y == 'axisx':
                            output.append(req_sensor.AxisX.lower())
                        elif y == "axisy":
                            output.append(req_sensor.AxisY.lower())
                        elif y == "axisz":
                            output.append(req_sensor.AxisZ.lower())
                        else:
                            output.append(None)
        except Exception as ex:
            vanalytics_data_logger.error(
                f"failed to get equipment axis details for the sensor_id: {sensor_id}", exc_info=True)
        finally:
            return req_sensor

    @classmethod
    def parse_rawdata(cls, data):
        try:
            # type_info = type(data)
            if isinstance(data, dict):
                d = str(data["v"]) + "$T$" + str(data["t"])
            else:
                d = json.loads(data)
                d = str(d["v"]) + "$T$" + str(d["t"])
            return d
        except Exception as ex:
            vanalytics_data_logger.error(f"ERROR: failed to parse {data}")
            print(f"ERROR: method: vanalytics_data.py - parse_rawdata, failed to parse {data}, with ex {ex}")

    @classmethod
    def parse_fft_rawdata(cls, data):
        try:
            if isinstance(data, dict):
                d = str(data["v"])
            else:
                d = json.loads(data)
                d = d["v"]
            return d
        except Exception as ex:
            vanalytics_data_logger.error(f"ERROR: failed to parse {data}")
            print(f"ERROR: method: vanalytics_data.py - parse_fft_rawdata, failed to parse {data}, with ex: {ex}")
       
    @classmethod    
    def process_fft_data(cls, data):
        if not isinstance(data, list) or len(data) < 1:
            return None
        
        try:
            item = json.loads(data[0])
            start_time = item['stime']

            item = json.loads(data[-1])
            end_time = item['etime']

            fft_list = []
            for x in data:
                val = json.loads(x)
                val = val['f']
                fft_list.append(val)
            
            return start_time, end_time, fft_list
        except Exception as ex:
            print(f"Error in method: vanalytics_data.py - process_fft_data, with ex: {ex}")
    
    @classmethod    
    def process_acc_data(cls, data):
        if not isinstance(data, list) or len(data) < 1:
            return None
        try:
            acc_list=[]
            for x in data:
                val_acc=x.split("$T$")[0]
                val_acc=float(val_acc)
                acc_list.append(val_acc)
            return acc_list
        except Exception as ex:
            print(f"Error in method: vanalytics_data.py - process_acc_data, with ex {ex}")
    
    @classmethod    
    def process_velocity_data(cls, data):
        
        try:
            velo_list=[]
            for x in data:
                val = float(x.split("$T$")[0])
                velo_list.append(val)
            #avg_velocity = np.mean(velo_list)
            return velo_list
        except Exception as ex:
            print(f"Error in method: vanalytics_data.py - process_velocity_data, with ex {ex}")
    
    @classmethod    
    def process_rms_data(cls, data):
        try:
            rms_list=[]
            for x in data:
                val =float(x.split("$T$")[0])
                rms_list.append(val)
            return rms_list
        except Exception as ex:
            print(f"Error in method: vanalytics_data.py - process_rms_data, with ex {ex}")
    
    @classmethod
    def clear_sensordata_lookup(cls, sensor_id):
        if sensor_id in CommonFeatures.sensordata_lookup:
            del CommonFeatures.sensordata_lookup[sensor_id]

    @classmethod
    def reset_sensor_defaultstate(cls, sensor_id, health):
        state = CommonFeatures.sensor_store[sensor_id]['H']
        state['state'] = health
        if health == 'good' or health == 'unknown':
            state['ts'] = time.time()
            faults = state['faults']
            faults['bearing'] = [0, 0, 0]
            faults['gear'] = [0, 0, 0]
            faults['misalignment'] = [0, 0, 0]
            faults['looseness'] = [0, 0, 0]
            faults['unbalance'] = [0, 0, 0]

    @classmethod
    def delete_unusedobjects(cls):
        print(f"Objects to clean: {CommonFeatures.cleanup_objects}")
        for sensor_id in CommonFeatures.cleanup_objects:
            if sensor_id in CommonFeatures.sensordata_lookup:
                del CommonFeatures.sensordata_lookup[sensor_id]
            CommonFeatures.cleanup_objects.remove(sensor_id)

class Axis:
    def __init__(self):
        self.x = []
        self.y = []
        self.z = []

class VibrationParam:
    def __init__(self):
        self.Fft = Axis()
        self.Rms = Axis()
        self.Velocity = Axis()
        self.Displacement = Axis()
        self.Acc = Axis()
        self.VelocityRms = Axis()

class VsensStreamProcessor:
    def __init__(self, sensorID, equipmentID):
        self.SensorID = sensorID
        self.EquipmentID = equipmentID
        self.StreamData = VibrationParam()
        self.WindowSize = None
        self.NoOfSamples = None
        self.SamplingFrequency = None
        self.Window = 0
        self.SensorMode = "cb"

        self.TempStore = {}
        self.BeingProcessed = False

        if CommonFeatures.sensor_store[self.SensorID]['H'] is None:
            CommonFeatures.sensor_store[self.SensorID]['H'] = {'state': 'unknown', 'ts': time.time(), 'count': 0, 'faults': {'bearing': [0, 0, 0], 'gear': [0, 0, 0],'unbalance': [0, 0, 0],'misalignment': [0, 0, 0],'looseness': [0, 0, 0]}}

    def update_dataset(self):
        try:
            output = CommonFeatures.getSensorMetadata(
            self.SensorID, ['numberofsamples', 'windowsize', 'samplingfrequency', 'sensormode'])
            mode = None
            if output is not None and len(output) == 4:
                self.NoOfSamples = output[0]
                self.WindowSize = output[1]
                self.SamplingFrequency = output[2]
                mode = output[3]

            if self.NoOfSamples is not None:
                self.NoOfSamples = int(self.NoOfSamples[0])
            else:
                self.NoOfSamples = int(
                    CommonFeatures.main_config["default_meta_values"]["numberofsamples"])

            if self.WindowSize is not None:
                self.WindowSize = int(self.WindowSize[0])
            else:
                self.WindowSize = int(
                    CommonFeatures.main_config["default_meta_values"]["windowsize"])
            
            if self.SamplingFrequency is not None:
                self.SamplingFrequency = int(self.SamplingFrequency[0])
            else:
                self.SamplingFrequency = int(
                    CommonFeatures.main_config["default_meta_values"]["samplingfrequency"])
                
            if mode is not None:
                self.SensorMode = mode[0]

            # test data
            #self.NoOfSamples = 8192
            #self.WindowSize = 8192
            #self.SamplingFrequency = 6400

            self.Window = int(self.NoOfSamples/self.WindowSize)
            return 0
        except Exception as ex:
            vanalytics_data_logger.error(
                f"Error while updating dataset information for Sensor: {self.SensorID}", exc_info=True)

    def axis_selection(self):
        pass
    
    def axisdetails(self,equipment_id,sensor_id):
        try:
            sensorsdata = CommonFeatures.equipment_store[equipment_id]['E']
            sens=sensorsdata.AttachedSensors
            sensor_details = next((x for x in sens if x.SensorMacID == sensor_id), None)
            
            if (sensor_details.AxisX=='HORIZONTAL_R') and (sensor_details.AxisY=='VERTICAL_R') and (sensor_details.AxisZ=='AXIAL') :
                #print("data is mounted axially")
                dataaxis='axial'
            if (sensor_details.AxisX=='VERTICAL_R') and (sensor_details.AxisY=='HORIZONTAL_R') and (sensor_details.AxisZ=='AXIAL'):
                #print("data is mounted horizontal") 
                dataaxis='horizontal'
            if (sensor_details.AxisX=='AXIAL') and (sensor_details.AxisY=='VERTICAL_R') and (sensor_details.AxisZ=='HORIZONTAL_R'):
                #print("data is mounted vertically")  
                dataaxis='vertical'
            return dataaxis
        except Exception as e:
            print(f"Error in method: vanalytics_data.py - axisdetails, with ex: {e}")
    
    def store_data(self, tag_type, raw_data):
        if self.SensorMode == 'cc':            
            if tag_type.startswith("V_RMS"):                
                raw_data = CommonFeatures.parse_rawdata(raw_data)
                if raw_data is None:
                    return

                if tag_type == "V_RMSX":
                    self.StreamData.VelocityRms.x.append(raw_data)
                elif tag_type == "V_RMSY":
                    self.StreamData.VelocityRms.y.append(raw_data)
                elif tag_type == "V_RMSZ":
                    self.StreamData.VelocityRms.z.append(raw_data)
        
        if tag_type.startswith("VELOCITY"):
            raw_data = CommonFeatures.parse_rawdata(raw_data)
            if raw_data is None:
                return
        
            if tag_type == "VELOCITYX":
                self.StreamData.Velocity.x.append(raw_data)
            elif tag_type == "VELOCITYY":
                self.StreamData.Velocity.y.append(raw_data)
            elif tag_type == "VELOCITYZ":
                self.StreamData.Velocity.z.append(raw_data)

        elif tag_type.startswith("FFT"):
            if self.SensorMode == 'cc':
                return
            
            raw_data = CommonFeatures.parse_fft_rawdata(raw_data)
            if raw_data is None:
                return
            
            if tag_type == "FFTX":
                self.StreamData.Fft.x.append(raw_data)
            elif tag_type == "FFTY":
                self.StreamData.Fft.y.append(raw_data)
            elif tag_type == "FFTZ":
                self.StreamData.Fft.z.append(raw_data)
            
        elif tag_type.startswith("ACC"):
            raw_data = CommonFeatures.parse_rawdata(raw_data)
            if raw_data is None:
                return

            if tag_type == "ACCX":
                self.StreamData.Acc.x.append(raw_data)
            elif tag_type == "ACCY":
                self.StreamData.Acc.y.append(raw_data)
            elif tag_type == "ACCZ":
                self.StreamData.Acc.z.append(raw_data)

        elif tag_type.startswith("RMS"):
            raw_data = CommonFeatures.parse_rawdata(raw_data)
            if raw_data is None:
                return

            if tag_type == "RMSX":
                self.StreamData.Rms.x.append(raw_data)
            elif tag_type == "RMSY":
                self.StreamData.Rms.y.append(raw_data)
            elif tag_type == "RMSZ":
                self.StreamData.Rms.z.append(raw_data)
        
        else:
            return

    def check_conditions_for_algo_process(self, is_time_based=False):
        if is_time_based:
            try:
                if self.SensorMode == 'cc' and len(self.StreamData.VelocityRms.x) > 0:
                    packet = self.StreamData.VelocityRms.x[0]
                    packet = int(packet.split("$T$")[1])
                    packet = int(str(packet)[:10]) #int(packet % 10000000000)
                    now = int(str(time.time())[:10])
                    diff = (now - packet)
                    if diff >= 60:
                        print(f"All data is not received for sensor: {self.SensorID}, destroying data")
                        CommonFeatures.cleanup_objects.append(self.SensorID)
                    
                    return False
                
                packet = self.StreamData.Acc.x[0]
                packet = int(packet.split("$T$")[1])
                packet = int(str(packet)[:10]) #int(packet % 10000000000)
                now = int(str(time.time())[:10])
                diff = (now - packet)/60
                if diff >= 4:
                    print(f"All data is not received for sensor: {self.SensorID}, destroying data")
                    CommonFeatures.cleanup_objects.append(self.SensorID)
                    
                return False
            except Exception as ex:
                print(f"Error in method: vanalytics_data.py - check_conditions_for_algo_process (is_time_based), with ex: {ex}")
        else:
            try:
                if self.SensorMode == 'cc':
                    if (len (self.StreamData.VelocityRms.x) >= 9 and len (self.StreamData.VelocityRms.y) >= 9 
                            and len (self.StreamData.VelocityRms.z) >= 9 and len(self.StreamData.Rms.x) >= 9 
                            and len(self.StreamData.Rms.y) >= 9 and len(self.StreamData.Rms.z) >=9):
                        return True
                    else:
                        return False
                
                if (len(self.StreamData.Fft.x) >= self.Window and len(self.StreamData.Fft.y) >= self.Window
                        and len(self.StreamData.Fft.z) >= self.Window and len(self.StreamData.Velocity.x) >= self.Window
                        and len(self.StreamData.Velocity.y) >= self.Window and len(self.StreamData.Velocity.z) >= self.Window
                        and len(self.StreamData.Rms.x) >= self.Window
                        and len(self.StreamData.Rms.y) >= self.Window and len(self.StreamData.Rms.z) >= self.Window
                        and len(self.StreamData.Acc.x) >= self.NoOfSamples and len(self.StreamData.Acc.y) >= self.NoOfSamples
                        and len(self.StreamData.Acc.z) >= self.NoOfSamples):
                    return True
                else:
                    return False
            except Exception as ex:
                print(f"Error in method: vanalytics_data.py - check_conditions_for_algo_process (is_time_based, else), with ex: {ex}")

    def update_temp_data(self, items):
        if items is None:
            items = ["powerOfMotor", "innerDiameterDriveEnd", "noOfTeethOnPinion", "outerDiameterDriveEnd", "maximumRPM","bearingPartDriveEnd","numberOfBallOrRollerDriveEnd","contactAngleDriveEnd"]
        
        output = CommonFeatures.getEquipmentMetaData(self.EquipmentID, items)
        
        self.TempStore["power"] = None
        self.TempStore["shaftPosition"] = None
        self.TempStore["pinionTeeth"] = None
        self.TempStore["bearingPartNo"] = None
        self.TempStore["maxRpm"] = None
        self.TempStore["numberOfBalls"] = None
        self.TempStore["innerDiameter"] = None
        self.TempStore["outerDiameter"] = None
        self.TempStore["angle"] = None
        #print(output[0][0] + " " + output[2][0] + " "+ output[4][0])

        #test purpose
        #self.TempStore["power"] = 800
        #self.TempStore["shaftPosition"] = "horizontal"
        #self.TempStore["pinionTeeth"] = 32
        #self.TempStore["bearingPartNo"] = "22410 CC/W23"
        #self.TempStore["maxRpm"] = 997

        try:
            if len(items) == len(output):            
                if output[0][0] is not None:
                    t = output[0][0].strip()
                    if len(t) > 0:
                        self.TempStore["power"] = float(t)
                
                if output[1][0] is not None:
                    t = output[1][0].strip()
                    if len(t) > 0:
                        self.TempStore["innerDiameter"] = t            
                
                if output[2][0] is not None:
                    t = output[2][0].strip()
                    if len(t) > 0:
                        self.TempStore["pinionTeeth"] = int(t)
                if output[3][0] is not None:
                    t = output[3][0].strip()
                    if len(t) > 0:
                        self.TempStore["outerDiameter"] = t   
                            
                if output[5][0] is not None:
                    t = output[5][0].strip()
                    if len(t) > 0:
                        self.TempStore["bearingPartNo"] = t
                
                if output[6][0] is not None:
                    t = output[6][0].strip()
                    if len(t) > 0:
                        self.TempStore["numberOfBalls"] = int(t)
                if output[7][0] is not None:
                    t = output[7][0].strip()
                    if len(t) > 0:
                        self.TempStore["angle"] = float(t)
                if output[4][0] is not None:
                    t = output[4][0].strip()
                    if len(t) > 0:
                        self.TempStore["maxRpm"] = int(t)

            self.TempStore["power"] = 0.75
        except Exception as ex:
            print(f"Error in method: vanalytics_data.py - update_temp_data, with ex: {ex}")
        
    def process_burst(self):
        if self.BeingProcessed == True:
            return
        
        self.BeingProcessed = True
        try:
            self.update_temp_data(None)
            print(f"Info: Eq: {self.EquipmentID} | sen: {self.SensorID} | mode: {self.SensorMode}")
            vsens_axis=self.axisdetails(self.EquipmentID, self.SensorID)
            if vsens_axis=='axial':
                if self.SensorMode == 'cb':
                    parsed_fft_horizontal = CommonFeatures.process_fft_data(self.StreamData.Fft.x)
                    parsed_fft_vertical = CommonFeatures.process_fft_data(self.StreamData.Fft.y)
                    parsed_fft_axial = CommonFeatures.process_fft_data(self.StreamData.Fft.z)
                    
                    parsed_acc_horizontal = CommonFeatures.process_acc_data(self.StreamData.Acc.x)
                    parsed_acc_vertical = CommonFeatures.process_acc_data(self.StreamData.Acc.y)
                    parsed_acc_axial = CommonFeatures.process_acc_data(self.StreamData.Acc.z)

                parsed_avg_velo_horizontal = CommonFeatures.process_velocity_data(self.StreamData.Velocity.x)
                parsed_velo_vertical = CommonFeatures.process_velocity_data(self.StreamData.Velocity.y)
                parsed_velo_axial = CommonFeatures.process_velocity_data(self.StreamData.Velocity.z)

                parsed_rms_horizontal = CommonFeatures.process_rms_data(self.StreamData.Rms.x)
                parsed_rms_vertical = CommonFeatures.process_rms_data(self.StreamData.Rms.y)
                parsed_rms_axial = CommonFeatures.process_rms_data(self.StreamData.Rms.z)
                
            elif vsens_axis=='horizontal':
                if self.SensorMode == 'cb':
                    parsed_fft_horizontal = CommonFeatures.process_fft_data(self.StreamData.Fft.y)
                    parsed_fft_vertical = CommonFeatures.process_fft_data(self.StreamData.Fft.x)
                    parsed_fft_axial = CommonFeatures.process_fft_data(self.StreamData.Fft.z)
                    
                    parsed_acc_horizontal = CommonFeatures.process_acc_data(self.StreamData.Acc.y)
                    parsed_acc_vertical = CommonFeatures.process_acc_data(self.StreamData.Acc.x)
                    parsed_acc_axial = CommonFeatures.process_acc_data(self.StreamData.Acc.z)

                parsed_avg_velo_horizontal = CommonFeatures.process_velocity_data(self.StreamData.Velocity.y)
                parsed_velo_vertical = CommonFeatures.process_velocity_data(self.StreamData.Velocity.x)
                parsed_velo_axial = CommonFeatures.process_velocity_data(self.StreamData.Velocity.z)

                parsed_rms_horizontal = CommonFeatures.process_rms_data(self.StreamData.Rms.y)
                parsed_rms_vertical = CommonFeatures.process_rms_data(self.StreamData.Rms.x)
                parsed_rms_axial = CommonFeatures.process_rms_data(self.StreamData.Rms.z)
            else:
                if self.SensorMode == 'cb':
                    parsed_fft_horizontal = CommonFeatures.process_fft_data(self.StreamData.Fft.z)
                    parsed_fft_vertical = CommonFeatures.process_fft_data(self.StreamData.Fft.y)
                    parsed_fft_axial = CommonFeatures.process_fft_data(self.StreamData.Fft.x)
                    
                    parsed_acc_horizontal = CommonFeatures.process_acc_data(self.StreamData.Acc.z)
                    parsed_acc_vertical = CommonFeatures.process_acc_data(self.StreamData.Acc.y)
                    parsed_acc_axial = CommonFeatures.process_acc_data(self.StreamData.Acc.x)

                parsed_avg_velo_horizontal = CommonFeatures.process_velocity_data(self.StreamData.Velocity.z)
                parsed_velo_vertical = CommonFeatures.process_velocity_data(self.StreamData.Velocity.y)
                parsed_velo_axial = CommonFeatures.process_velocity_data(self.StreamData.Velocity.x)

                parsed_rms_horizontal = CommonFeatures.process_rms_data(self.StreamData.Rms.z)
                parsed_rms_vertical = CommonFeatures.process_rms_data(self.StreamData.Rms.y)
                parsed_rms_axial = CommonFeatures.process_rms_data(self.StreamData.Rms.x)
        

            if self.SensorMode == 'cc':
                vmrs = CommonFeatures.process_velocity_data(self.StreamData.VelocityRms.x)
                vrms_x = np.mean(vmrs)
                vmrs = CommonFeatures.process_velocity_data(self.StreamData.VelocityRms.y)
                vrms_y = np.mean(vmrs)
                vmrs = CommonFeatures.process_velocity_data(self.StreamData.VelocityRms.z)
                vrms_z = np.mean(vmrs)

            # output [fft_average 0, rms 1, amplitude 2, frequency 3, rms_amplitude 4, rms_frequency 5]
            if self.SensorMode == 'cb':
                avg_fft_horizontal = fft_cal.parse_fft_rawdata(self.SamplingFrequency, parsed_fft_horizontal[2])
                avg_fft_vertical = fft_cal.parse_fft_rawdata(self.SamplingFrequency, parsed_fft_vertical[2])
                avg_fft_axial = fft_cal.parse_fft_rawdata(self.SamplingFrequency, parsed_fft_axial[2])

                fft_bearing_horizontal = avg_fft_horizontal[2]
                fft_bearing_vertical = avg_fft_vertical[2]
                fft_bearing_axial = avg_fft_axial[2]

                frequency_horizontal = avg_fft_horizontal[3]
                frequency_vertical = avg_fft_vertical[3]
                frequency_axial = avg_fft_axial[3]

                rms_horizontal = avg_fft_horizontal[1]
                rms_vertical = avg_fft_vertical[1]
                rms_axial = avg_fft_axial[1]

                horizontal_amp_horizontal= avg_fft_horizontal[2]
                horizontal_amp_vertical = avg_fft_vertical[2]
                horizontal_amp_axial = avg_fft_axial[2]

                fft_horizontal = avg_fft_horizontal[0]
                fft_vertical = avg_fft_vertical[0]
                fft_axial = avg_fft_axial[0]
           

            
            
            if self.SensorMode == 'cc':
                rms = max([vrms_x, vrms_y, vrms_z])
            else:
                rms = parsed_avg_velo_horizontal[0]
                
                #   get the RPM
                print(f"RPM value given for equipment {self.EquipmentID} is {self.TempStore['maxRpm']}")
                if self.TempStore["maxRpm"] is not None:
                    rpm_from_vib_X = op_rpm.RpmFromVibration(self.SamplingFrequency, self.WindowSize, self.TempStore["maxRpm"],
                                                           self.SensorID, self.EquipmentID, fft_horizontal)
                    operating_rpm_X = rpm_from_vib_X.Speed_Detection()
                    del rpm_from_vib_X

            # machine on off
            # onOff = algo_onoff.MachineStatus(fft_X, self.SamplingFrequency, self.EquipmentID, self.SensorID)
            # onOff = algo_onoff.MachineStatus(rms_horizontal, self.SamplingFrequency, self.EquipmentID, self.SensorID)
            # onOff = algo_onoff.MachineStatus(parsed_rms_horizontal[0], self.SamplingFrequency, self.EquipmentID, self.SensorID)
            onOff = algo_onoff.MachineStatus(rms, self.SamplingFrequency, self.EquipmentID, self.SensorID)
            onOff_output = onOff.check_machine_status()
            del onOff

            if onOff_output == 0:
                print(f"{self.EquipmentID} is currently not running. received rms value: {rms}")
                self.dispose()
                return

            # velocity severity            
            if self.TempStore['power'] is not None:                
                print(f"Checking velocity severity for equipment: {self.EquipmentID}, sensor {self.SensorID}, power {self.TempStore['power']}, velocity {rms}")
                severity = algo_severity.velocity_severity(
                    self.TempStore["power"], rms, self.EquipmentID, self.SensorID)
                severity_output = severity.velocity_total_check()
            else:
                print(f"Skipping severity for equipment: {self.EquipmentID}, sensor {self.SensorID}, as power is {self.TempStore['power']}, velocity {rms}")
                severity_output = -1
            
            
            
            
            if severity_output == 0:
                CommonFeatures.reset_sensor_defaultstate(self.SensorID, 'good')
                count = CommonFeatures.sensor_store[self.SensorID]['H']['count']
                print(f"{self.EquipmentID}/{self.SensorID} is in Good state, skipping algorithm testing.")
                count = count + 1
                if count < 3:
                    final_output = ["0","5","9","11", "13"]
                    data = [self.EquipmentID, self.SensorID, "FO",
                            json.dumps(final_output) + "$T$" + str(time.time() * 1000)]
                    v_helper.helper.data_to_publish.append(data)
                else:
                    count = 3
                CommonFeatures.sensor_store[self.SensorID]['H']['count'] = count
                return
            elif severity_output == -1:
                CommonFeatures.reset_sensor_defaultstate(self.SensorID, 'unknown')
                print(f"{self.EquipmentID}/{self.SensorID} Power input is missing cannot determine the machine state, skipping algorithm testing.")
                return
            else:
                 state = CommonFeatures.sensor_store[self.SensorID]['H']
                 if state['state'] != 'bad':
                    state['state'] = 'bad'
                    state['ts'] = time.time()
                    state['count'] = 0
            
            if self.SensorMode == 'cc':
                if (rms > 4):
                    faults = CommonFeatures.sensor_store[self.SensorID]['H']['faults']['unbalance']
                    if faults[0] == 0:
                        faults[0] = 1
                        faults[1] = time.time()
                        faults[2] = int(faults[2]) + 1
                        final_output = ["10"]
                        data = [self.EquipmentID, self.SensorID, "FO",
                                json.dumps(final_output) + "$T$" + str(time.time() * 1000)]
                        v_helper.helper.data_to_publish.append(data)
                    else:
                        faults[2] = int(faults[2]) + 1
                        if int(faults[2]) == 2:
                            faults[1] = time.time()
                            final_output = ["10"]
                            data = [self.EquipmentID, self.SensorID, "FO",
                                    json.dumps(final_output) + "$T$" + str(time.time() * 1000)]
                            v_helper.helper.data_to_publish.append(data)
                        else:
                            faults[2] = 3                        
                                
                return
            
            return

            # if rpm value is none, return from here
            
            # bearing
            bearing_output = []
            try:
                bearing_obj = algo_bearing.Bearing(
                    self.TempStore["numberOfBalls"], self.TempStore["innerDiameter"], self.TempStore["outerDiameter"], 
                    self.TempStore["angle"], self.TempStore["bearingPartNo"], operating_rpm_X, self.SamplingFrequency, 
                    self.NoOfSamples, self.WindowSize, self.EquipmentID, self.SensorID, fft_horizontal, fft_vertical, fft_axial,frequency_vertical,avg_fft_horizontal[5], avg_fft_vertical[5], avg_fft_axial[5], rms_vertical)
                bearing_output = bearing_obj.bearing_total_check()
                if bearing_output is None:
                    bearing_output = []
            except Exception as ex:
                print(f"Error occured during: vanalytics_data.py - bearing_output, with ex: {ex}")
            
            # gearbox
            gear_output = []
            try:
                gear_obj = algo_gearbox.Gear(operating_rpm_X,self.TempStore["pinionTeeth"], self.SamplingFrequency,
                                             self.NoOfSamples, self.WindowSize, self.EquipmentID, self.SensorID,fft_horizontal, fft_vertical, fft_axial,frequency_vertical,avg_fft_horizontal[5], avg_fft_vertical[5], avg_fft_axial[5], rms_vertical)
                gear_output = gear_obj.gmff_total_check()
                if gear_output is None:
                    gear_output = []
            except Exception as ex:
                print(f"Error occured during: vanalytics_data.py - gear_output, with ex: {ex}")
            
            # misalignment
            misalignment_output = []
            try:
                misalignment_obj = algo_misalignment.Misalignment_Analysis(
                    self.SamplingFrequency, self.NoOfSamples, self.WindowSize, operating_rpm_X, self.SensorID,
                    self.EquipmentID, fft_horizontal, fft_vertical, fft_axial, frequency_horizontal, frequency_vertical, frequency_axial)
                misalignment_output = misalignment_obj.mis_total_axis_check()
                if misalignment_output is None:
                    misalignment_output = []
            except Exception as ex:
                print(f"Error occured during: vanalytics_data.py - misalignment_output, with ex: {ex}")
            
            # looseness
            looseness_output = []
            try:
                looseness_obj = algo_looseness. Looseness_Analysis(
                    self.SamplingFrequency, self.NoOfSamples, self.WindowSize, operating_rpm_X, self.SensorID,
                    self.EquipmentID, fft_horizontal, fft_vertical, fft_axial, frequency_horizontal, frequency_vertical, frequency_axial)
                looseness_output = looseness_obj.Looseness_Total_Check()
                if looseness_output is None:
                    looseness_output = []
            except Exception as ex:
                print(f"Error occured during: vanalytics_data.py - looseness_output, with ex: {ex}")
            
            # unbalance
            unbalance_output = []
            try:
                unbalance_obj = algo_unbalance.unbalance(
                    self.SamplingFrequency, self.NoOfSamples, self.WindowSize, operating_rpm_X, self.SensorID,
                    self.EquipmentID,fft_horizontal, fft_vertical, fft_axial,rms_horizontal)
                unbalance_output = unbalance_obj.unbalance_total_check()
                if unbalance_output is None:
                    unbalance_output = []
            except Exception as ex:
                print(f"Error occured during: vanalytics_data.py - unbalance_output, with ex: {ex}")
            
            temp_list = bearing_output + gear_output + misalignment_output + looseness_output + unbalance_output
            final_output = [str(x) if isinstance(x, int) else x for x in temp_list]
            # formatted_output = {}
            # formatted_output['d'] = final_output
            data = [self.EquipmentID, self.SensorID, "FO",
                    json.dumps(final_output) + "$T$" + str(time.time() * 1000)]
            v_helper.helper.data_to_publish.append(data)
        except Exception as ex:
            print(f"Error occured during: vanalytics_data.py - final_fault_output, with ex: {ex}")
        finally:
            CommonFeatures.cleanup_objects.append(self.SensorID)
            print(f"Sensor to cleanup: {CommonFeatures.cleanup_objects}")

    def dispose(self):
        CommonFeatures.cleanup_objects.append(self.SensorID)

    def __del__(self):
        print('Object Destroyed...')
