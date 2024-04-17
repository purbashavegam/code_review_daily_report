import requests
import pandas as pd
import json
import logging
import time
from datetime import datetime
vegamview_api_url = "https://apps.vegam.co/iPAS_VegamViewService/VegamViewRestService.svc/GetHistoricalData"

payload = {"historyDataParamter": [{"signalIds": ["1389", "1394", "1399"], "fromTime": 1703676606972, "toTime": 1703680206972}]}

def fetch_vrms_temp_data(payload):

    try:

        print("hi................ inside vegam view call...................")
        print(payload, "---------------------------------------")
        vrms_temp_api_url = f"{vegamview_api_url}"
        response = requests.post(vrms_temp_api_url, json=payload)
        print(response.status_code, "*******************************")
        # print(response.text,type(response.text))
        print(type(response.text))
        response.raise_for_status()
        vrms_temp_data = response.json()
        return vrms_temp_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching VRMS/Temp data from VegamView API: {e}")
        return {}




def extract_v_and_t_from_api_data(api_data):
    extracted_data = []
    try:


        if isinstance(api_data, str):
            api_data = json.loads(api_data)
        print(len(api_data))
        print(api_data)

        for entry in api_data:
            print(len(entry))
            historical_data = entry.get("historicalData", [])

            for vtq_entry in historical_data:
                vtq_data = vtq_entry.get("vtq", [])

                signal_id = vtq_entry.get("signalId")
                v_values = [item.get("v") for item in vtq_data]
                t_values = [datetime.fromtimestamp(item.get("t") / 1000).strftime("%d/%m/%Y %I:%M %p") for item in
                            vtq_data]

                if v_values and t_values:
                    extracted_data.append({"signalId": signal_id, "v_values": v_values, "t_values": t_values})


    except Exception as a:
        print("error in extraction api data pre processing :", str(a))
    return extracted_data




data_vrms = fetch_vrms_temp_data(payload)
print(len(data_vrms),"step one done....")
extract_data = extract_v_and_t_from_api_data(data_vrms)

print(len(extract_data),"step two done.....")


def save_data_to_excel_for_alert(extracted_data, output_file_prefix, sheet_name_prefix, mac_id):
    try:
        chunks_of_4 = [extracted_data[i:i + 4] for i in range(0, len(extracted_data), 4)]
        # print(output_file_prefix,"----------------------")
        # print("chunk of 4 is ",len(chunks_of_4))

        if len(chunks_of_4) > 0:
            for i, chunk in enumerate(chunks_of_4, start=1):
                # print("i is",i)
                output_file_path = f'{output_file_prefix}_{mac_id}.xlsx'
                with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
                    for j, entry in enumerate(chunk, start=1):
                        df = pd.DataFrame({'DateTime': entry['t_values'], 'Value': entry['v_values']})
                        exploded_df = df.explode('DateTime').explode('Value')

                        # Extract tag_ids from the entry dictionary
                        tag_ids = entry.get(
                            "signalId")  # ('tag_ids', [])  # Adjust the key based on your actual data structure
                        # print(tag_ids)

                        if j == 1:
                            name = "X_Axis"
                        elif j == 2:
                            name = "Y_Axis"
                        elif j == 3:
                            name = "Z_Axis"

                        sheet_name = f'{mac_id}_{tag_ids}_{name}'  # Each sheet contains one set of 4 signal IDs
                        exploded_df.to_excel(writer, index=False, header=True, sheet_name=sheet_name)

                df_if = pd.read_excel(output_file_path)
                num_rows = df_if.shape[0]

                logging.info(f"Separated values saved to {output_file_path}")
                logging.info(f'The Excel file has {num_rows} rows.')
        else:  # elif len(chunks_of_4) == 0:
            logging.info("no data...")
            output_file_path = f'{output_file_prefix}_{mac_id}.xlsx'
            with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:

                for j in range(1, 4):  # Assuming you always want 3 sheets    # if no data add logic
                    if j == 1:
                        name = "X_Axis"
                    elif j == 2:
                        name = "Y_Axis"
                    elif j == 3:
                        name = "Z_Axis"
                    sheet_name = f'{mac_id}_empty_sheet_{name}'
                    pd.DataFrame().to_excel(writer, index=False, header=True, sheet_name=sheet_name)

            df_else = pd.read_excel(output_file_path)
            num_rows = df_else.shape[0]
            logging.info(f"Empty Excel saved to {output_file_path}")
            logging.info(f'The Excel file has {num_rows} rows.')


    except Exception as e:
        logging.error(f"An error occurred in ExtractSensorData save_data_to_excel_for_alert: {str(e)}")
