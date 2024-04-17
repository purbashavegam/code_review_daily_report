import requests
import pandas as pd
import json
import logging
import time
from datetime import datetime
from functools import wraps



def retry(num_retry, sleep_sec):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            """A wrapper function"""
            for retry_num in range(1, num_retry+1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print("Number of retry ", retry_num)
                    logging.error(
                        f'Attempting retry -----{retry_num}----for Extract Sensor Data -------exception{str(e)}')
                    time.sleep(sleep_sec)
            return {}

        return wrapper

    return decorator

class ExtractSensorData:
    # supriya
    def __init__(self, vegamview_api_url):
        try:
            """
            Initialize the ExtractSensorData class with the VegamView API URL and ExtractMetaData instance.

            Parameters:
            - vegamview_api_url (str): The URL of the VegamView API.
            - metadata_extractor (ExtractMetaData): An instance of ExtractMetaData for UUID extraction. #why???
            """
            self.vegamview_api_url = vegamview_api_url
        except Exception as e:
            logging.error(f"An error occurred in ExtractSensorData init: {str(e)}")


    @retry(5, 30)
    def fetch_vrms_temp_data(self, payload):
        """
        Fetch VRMS/Temp data from VegamView API according to the provided payload.

        Parameters:
        - payload (dict): The payload containing data for the API request.

        Returns:
        - dict: VRMS/Temp data.
        """
        try:

            print("hi................ inside vegam view call...................")
            print(payload, "---------------------------------------")
            vrms_temp_api_url = f"{self.vegamview_api_url}"
            response = requests.post(vrms_temp_api_url, json=payload)
            print(response.status_code, "*******************************")
            # print(response.text,type(response.text))
            print(type(response.text))
            response.raise_for_status()
            vrms_temp_data = response.json()
            return vrms_temp_data
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching VRMS/Temp data from VegamView API: {e}")
            # print(f"Error fetching VRMS/Temp data from VegamView API: {e}")
            raise e

    def fetch_and_store_vrms_temp_data(self, uuids_list):
        """
        Fetch and store VRMS/Temp data for UUIDs extracted by ExtractMetaData.
        """
        uuids = []  # have a list

        for uuid in uuids:
            payload = {"uuid": uuid}  # Adjust the payload structure based on your API requirements
            vrms_temp_data = self.fetch_vrms_temp_data(payload)
            print(len(vrms_temp_data), "is it zero??")
            excel_filename = f'vrms_temp_data_{uuid}.xlsx'
            self.store_data_to_excel(vrms_temp_data, excel_filename)

    @retry(5, 30)
    def call_api_and_extract_data(self,api_url, payload, max_retries):
        try:
            response = requests.post(api_url, json=payload, timeout=10)  # Set a timeout (in seconds)

            if response.status_code == 200:
                api_data_string = response.text
                api_data = json.loads(api_data_string)
                return api_data
            else:
                print(f"Error: {response.status_code} - {response.text}")
                logging.error(f"Error: {response.status_code} - {response.text}")
                raise
        except requests.exceptions.Timeout:
            print(f"Error: Timeout occurred while connecting to the API. Retrying... )")
            logging.error(f"Error: Timeout occurred while connecting to the API. Retrying... )")
            raise requests.exceptions.Timeout
        except Exception as e:
            print(f"Error: {str(e)}")
            logging.error(f"Error: {str(e)}")
            raise e

    def save_data_to_excel_in_batches(self, extracted_data, output_file_prefix, sheet_name_prefix, sensor_mac_id):
        chunks_of_4 = [extracted_data[i:i + 4] for i in range(0, len(extracted_data), 4)]

        for i, chunk in enumerate(chunks_of_4, start=1):
            output_file_path = f'{output_file_prefix}_{i}.xlsx'
            with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
                for entry in chunk:
                    df = pd.DataFrame({'DateTime': entry['t_values'], 'Value': entry['v_values']})
                    exploded_df = df.explode('DateTime').explode('Value')
                    sheet_name = f'{sheet_name_prefix}_{entry["signalId"]}_{sensor_mac_id}'
                    exploded_df.to_excel(writer, index=False, header=True, sheet_name=sheet_name)

            print(f"Separated values saved to {output_file_path}")

    def save_data_to_excel_in_batchess(self, extracted_data, output_file_prefix):
        chunks_of_4 = [extracted_data[i:i + 4] for i in range(0, len(extracted_data), 4)]

        for i, chunk in enumerate(chunks_of_4, start=1):
            output_file_path = f'{output_file_prefix}_{i}.xlsx'
            with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
                for j, entry in enumerate(chunk, start=1):
                    df = pd.DataFrame({'DateTime': entry['t_values'], 'Value': entry['v_values']})
                    sheet_name = f'Sheet_{entry["signalId"]}_{j}'  # Each sheet contains one signal ID within a set of 4

                    exploded_df = df.explode('DateTime').explode('Value')
                    exploded_df.to_excel(writer, index=False, header=True, sheet_name=sheet_name)

            print(f"Separated values saved to {output_file_path}")

    def save_data_to_excel_in_batchesss(self, extracted_data, output_file_prefix, sensor_mac_ids):
        chunks_of_4 = [extracted_data[i:i + 4] for i in range(0, len(extracted_data), 4)]

        for i, chunk in enumerate(chunks_of_4, start=1):
            # Get the common sensor_mac_id for the current set of signal IDs
            current_sensor_mac_ids = [sensor_mac_ids.get(signal_id, "") for signal_id in chunk]
            common_sensor_mac_id = current_sensor_mac_ids[0] if all(
                sensor_mac_id == current_sensor_mac_ids[0] for sensor_mac_id in current_sensor_mac_ids) else ""

            output_file_path = f'{output_file_prefix}_Sensor_{common_sensor_mac_id}_{i}.xlsx'
            with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
                for j, entry in enumerate(chunk, start=1):
                    df = pd.DataFrame({'DateTime': entry['t_values'], 'Value': entry['v_values']})
                    exploded_df = df.explode('DateTime').explode('Value')
                    sheet_name = f'Sheet_{i}_{j}'  # Each sheet contains one set of 4 signal IDs
                    exploded_df.to_excel(writer, index=False, header=True, sheet_name=sheet_name)

            print(f"Separated values saved to {output_file_path}")

    def save_data_to_excel_in_batchees(self, extracted_data, output_file_prefix, sheet_name_prefix):
        chunks_of_4 = [extracted_data[i:i + 4] for i in range(0, len(extracted_data), 4)]

        for i, chunk in enumerate(chunks_of_4, start=1):
            output_file_path = f'{output_file_prefix}_{i}.xlsx'
            with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
                for j, entry in enumerate(chunk, start=1):
                    df = pd.DataFrame({'DateTime': entry['t_values'], 'Value': entry['v_values']})
                    exploded_df = df.explode('DateTime').explode('Value')

                    # Extract tag_ids from the entry dictionary
                    tag_ids = entry.get('tag_ids', [])  # Adjust the key based on your actual data structure

                    # Construct sheet name using tag_ids
                    sheet_name = f'{sheet_name_prefix}_{"_".join(tag_ids)}_{j}'  # Each sheet contains one set of 4 signal IDs
                    exploded_df.to_excel(writer, index=False, header=True, sheet_name=sheet_name)

            print(f"Separated values saved to {output_file_path}")

        # Check if there are any remaining signals not included in chunks of 4
        remaining_signals = extracted_data[len(chunks_of_4) * 4:]
        if remaining_signals:
            output_file_path = f'{output_file_prefix}_{i + 1}.xlsx'
            with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
                for k, entry in enumerate(remaining_signals, start=1):
                    df = pd.DataFrame({'DateTime': entry['t_values'], 'Value': entry['v_values']})
                    exploded_df = df.explode('DateTime').explode('Value')

                    # Extract tag_ids from the entry dictionary
                    tag_ids = entry.get('tag_ids', [])  # Adjust the key based on your actual data structure

                    # Construct sheet name using tag_ids
                    sheet_name = f'{sheet_name_prefix}_{"_".join(tag_ids)}_{k}'  # Each sheet contains the remaining signals
                    exploded_df.to_excel(writer, index=False, header=True, sheet_name=sheet_name)

            print(f"Separated values saved to {output_file_path}")

    # def save_data_to_excel_in_batches(self, extracted_data, output_file_prefix):
    #     # Create a single Excel file for each batch
    #     output_file_path = f'{output_file_prefix}.xlsx'
    #
    #     # Iterate over the batches and save each in a different sheet
    #     with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
    #         for i, entry in enumerate(extracted_data, start=1):
    #             df = pd.DataFrame({'DateTime': entry['t_values'], 'Value': entry['v_values']})
    #             exploded_df = df.explode('DateTime').explode('Value')
    #             sheet_name = f'Sheet_{entry["signalId"]}_{i}'  # Each sheet contains one signal ID with batch number
    #             exploded_df.to_excel(writer, index=False, header=True, sheet_name=sheet_name)
    #
    #     print(f"All separated values saved to {output_file_path}")

    def extract_v_and_t_from_api_data(self, api_data):  # using in alert
        extracted_data = []
        try:

            if isinstance(api_data, str):
                api_data = json.loads(api_data)
                # print("--------------------------")
                # print(api_data)

            for entry in api_data:
                historical_data = entry.get("historicalData", [])
                # print("****************************************************************************************")
                # print(historical_data)

                for vtq_entry in historical_data:
                    # print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
                    # print(vtq_entry)
                    vtq_data = vtq_entry.get("vtq", [])

                    signal_id = vtq_entry.get("signalId")
                    v_values = [item.get("v") for item in vtq_data]
                    t_values = [datetime.fromtimestamp(item.get("t") / 1000).strftime("%d/%m/%Y %I:%M %p") for item in
                                vtq_data]

                    # print(v_values)
                    # print(t_values)
                    if (not v_values and not t_values) or (v_values and not t_values) or (not v_values and t_values):
                        # print("kkkkkk::::::::::::::::::::::::::::")
                        logging.critical(f"data not present for the tag{signal_id}")
                        extracted_data.append({"signalId": signal_id, "v_values": v_values, "t_values": t_values})
                    if v_values and t_values:
                        # print("yoooooo...")
                        logging.info("all tag data present....")
                        extracted_data.append({"signalId": signal_id, "v_values": v_values, "t_values": t_values})

        except Exception as a:
            print("error in extraction api data pre processing :", str(a))
        return extracted_data

    def save_data_to_excel(self, data, excel_filename):
        """
        Save data to Excel file.

        Parameters:
        - data (list): List of dictionaries containing the data.
        - excel_filename (str): The name of the Excel file.
        """
        try:
            with pd.ExcelWriter(excel_filename, engine='xlsxwriter') as writer:
                for entry in data:
                    df = pd.DataFrame({'DateTime': entry['t_values'], 'Value': entry['v_values']})
                    exploded_df = df.explode('DateTime').explode('Value')
                    sheet_name = f'SignalID_{entry["signalId"]}'
                    exploded_df.to_excel(writer, index=False, header=True, sheet_name=sheet_name)
            print(f"Data saved to {excel_filename} successfully.")
        except Exception as e:
            print(f"Error saving data to Excel: {e}")

    def store_data_to_excel(self, data, excel_filename):
        """
        Store data to Excel file.

        Parameters:
        - data (dict): The data to be stored.
        - excel_filename (str): The name of the Excel file.
        """
        try:
            df = pd.DataFrame(data)
            df.to_excel(excel_filename, index=False)
            print(f"Data stored to {excel_filename} successfully.")
        except Exception as e:
            print(f"Error storing data to Excel: {e}")

    def save_dataa_to_excel(self, extracted_data, output_file_path, sheet_name, sensor_mac_id):
        with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
            for entry in extracted_data:
                df = pd.DataFrame({'DateTime': entry['t_values'], 'Value': entry['v_values']})
                exploded_df = df.explode('DateTime').explode('Value')
                sheet_name = f'{sheet_name}_{entry["signalId"]}_{sensor_mac_id}'
                exploded_df.to_excel(writer, index=False, header=True, sheet_name=sheet_name)

        print(f"Separated values saved to {output_file_path}")

    # supriya

    def save_data_to_excel_for_alert(self, extracted_data, output_file_prefix, sheet_name_prefix, mac_id):
        """

        {'vtq': [], 'signalId': 2391, 'totalCount': 0, 'samplingRate': 0, 'isFailedToFetchData': False, 'dataFetchErrormessage': None}
        {'vtq': [{'v': '19', 'q': 1, 't': 1703222315776, 'g': 0}, {'v': '23', 'q': 1, 't': 1703224518300, 'g': 0}, {'v': '27', 'q': 1, 't': 1703234603423, 'g': 0}, {'v': '26', 'q': 1, 't': 1703236260829, 'g': 0}],
         'signalId': 2374, 'totalCount': 0, 'samplingRate': 0, 'isFailedToFetchData': False, 'dataFetchErrormessage': None}


        """
        try:
            # print("________________________________________________________________________________")
            # print("________________________________________________________________________________")
            # print(len(extracted_data))
            chunks_of_4 = [extracted_data[i:i + 4] for i in range(0, len(extracted_data), 4)]
            # print(output_file_prefix,"----------------------")
            # print("chunk of 4 is ",len(chunks_of_4))

            if len(chunks_of_4) > 0:
                for i, chunk in enumerate(chunks_of_4, start=1):
                    # print("i is",i)
                    output_file_path = f'{output_file_prefix}_{mac_id}.xlsx'
                    with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
                        for j, entry in enumerate(chunk, start=1):
                            # print(entry['t_values'])
                            # print(entry['v_values'])
                            df = pd.DataFrame({'DateTime': entry['t_values'], 'Value': entry['v_values']})
                            # print(df)
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
                            elif j == 4:
                                name = "Temp"

                            sheet_name = f'{mac_id}_{tag_ids}_{name}'  # Each sheet contains one set of 4 signal IDs
                            exploded_df.to_excel(writer, index=False, header=True, sheet_name=sheet_name)
                            # avg_value = pd.to_numeric(exploded_df['Value']).dropna().mean()
                            # print(avg_value,'avgvaliueeeeeeeeeeeeeeee')

                    df_if = pd.read_excel(output_file_path)
                    # print(df_if,'df_if......................................................')
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
                        elif j == 4:
                            name = "Temp"
                        sheet_name = f'{mac_id}_empty_sheet_{name}'
                        pd.DataFrame().to_excel(writer, index=False, header=True, sheet_name=sheet_name)

                df_else = pd.read_excel(output_file_path)
                num_rows = df_else.shape[0]
                logging.info(f"Empty Excel saved to {output_file_path}")
                logging.info(f'The Excel file has {num_rows} rows.')


        except Exception as e:
            logging.error(f"An error occurred in ExtractSensorData save_data_to_excel_for_alert: {str(e)}")


