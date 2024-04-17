'''
OBJECTIVE : #MONTHLY
This file is required in case for the diff days if we use diff api, so it will take the responses from api day wise (1-2,2-3,3-4 etc)
and store in a text file and similarly for other api we will store in one text file.

'''


import json
import time

import requests
from datetime import datetime, timedelta
from Scripts.Trending.report.ExtractMetaData import ExtractMetaData

# Function to convert date to epoch timestamp

# def date_to_timestamp(date_str):
#     dt = datetime.strptime(date_str, '%Y-%m-%d')
#     return int(dt.timestamp()) * 1000  # Convert to milliseconds

# Function to make API call with given date range
api_url = "https://apps.vegam.co/iPAS_VegamViewService/VegamViewRestService.svc/GetHistoricalData"
def make_api_call(start_date, end_date, tags):
    # api_url = "http://apps.vegam.co:7013/storeapi/signaldata/GetHistoricalData"
    # payload = {"historyDataParamter": [
    #     {"signalIds": ["1575", "1580", "1585", "1568"],
    #      "fromTime": start_date, "toTime": end_date
    #      }
    # ]
    # }
    payload = {
        "historyDataParamter": [
            {"signalIds": tags, "fromTime": start_date, "toTime": end_date}
        ]
    }
    print(payload)
    response = requests.post(api_url, json=payload)
    time.sleep(5)
    # print(response.text)
    response_val = json.loads(response.text)
    return response_val

# Function to combine individual responses into one
def combine_responses(responses):
    combined_response = []

    for response in responses:
        combined_response.extend(response)

    return combined_response

# Define date range from March 1st, 2024 to March 15th, 2024
def datetime_to_timestamp(dt):
    return int(dt.timestamp()) * 1000  # Convert to milliseconds

# Function to generate date ranges from start time to end time with timestamps
def generate_date_ranges(start_time, end_time):
    date_ranges = []
    current_time = start_time

    while current_time < end_time:
        next_time = current_time + timedelta(days=1)
        date_ranges.append((datetime_to_timestamp(current_time), datetime_to_timestamp(next_time)))
        current_time = next_time

    return date_ranges

def combine_response_of_1day_basis_apicall(macid, topic_tags):
    # Convert date strings to datetime objects
    start_time_str = '21-03-2024 00:00:00'
    end_time_str = '01-04-2024 00:00:00'

    # ---------------- from direct start time to end time in one time call-------------------

    # start_time = int((datetime.strptime(start_time_str, '%d-%m-%Y %H:%M:%S')).timestamp()) * 1000
    # end_time = int((datetime.strptime(end_time_str, '%d-%m-%Y %H:%M:%S')).timestamp()) * 1000

    # payload = {
    #     "historyDataParamter": [
    #         {"signalIds": topic_tags, "fromTime": start_time, "toTime": end_time}
    #     ]
    # }
    # response = requests.post(api_url, json=payload)
    # print(response.status_code, "*******************************")
    # print(response.text,type(response.text))
    # print(type(response.text))
    # response.raise_for_status()
    # response_data = response.json()
    # response_data = [json.loads(response_data)]
    # ---------------- group 1time data fetching end here----------------


    # -----------------1day - 1day data fetching and keep in one file
    start_time = start_time_str
    end_time = end_time_str
    date_ranges = generate_date_ranges(start_time, end_time)
    # Define date ranges for API calls
    # for date_range in date_ranges:
    #     start_timestamp, end_timestamp = date_range
    #     response = make_api_call(start_timestamp, end_timestamp)
    #     # responses.append(response)

    # List to store individual responses
    responses = []

    # Make API calls for each date range
    for start_date, end_date in date_ranges:
        # time.sleep(5)
        print(f"api started from  {start_date} to {end_date}")
        response = make_api_call(start_date, end_date, topic_tags)
        # print(f"Response - {response}")
        responses.append(response)
    response_data = responses
    # -----------ended here 1day-1day----------------

    print(type(response_data))
    time.sleep(5)
    # print(responses)
    return response_data


for areas in ["CHP","Compressor House","Cooling Tower Area"]:
    obj = ExtractMetaData(
        "https://apps.vegam.co/Vegam_MaintenanceService/MaintenanceAnalyticsService.svc/DeployedSensors?siteID=26", 9,
        areas)
    # Call the method and store the result
    # result = obj.get_hierarchy_level_with_equipment_details_from_metadata()
    resp = obj.get_mac_ids_tags_for_report_with_temp()
    print(f"response from tags collection - {resp}")

    for item in resp:
        macid = list(item.keys())[0]  # Extract macid from dictionary
        topics = item[macid]  # Extract list of topic dictionaries
        topic_tags = [topic['Topic'] for topic in topics if 'Topic' in topic]  # Extract Topic values
        print(f"started for {macid}")
        responses = combine_response_of_1day_basis_apicall(macid, topic_tags)


        # Generate file name based on current hour, minute, and second
        file_name = f"C://Vegam//merged_json_response_21_01//2131_response_data_{macid}.txt"

        # Open the file in write mode
        with open(file_name, 'w') as file:
            # Write each data point to the file
            for data_point in responses:
                file.write(str(data_point) + '\n')

        print("Data saved successfully to:", file_name)






