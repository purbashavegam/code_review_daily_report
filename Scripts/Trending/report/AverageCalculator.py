import pandas as pd
# import numpy as np
# from pandas import to_datetime,DataFrame
import matplotlib.pyplot as plt
import json
from numpy import nan, int64
import os
from scipy.stats import linregress
import datetime
import logging
from datetime import timedelta
from matplotlib.ticker import MultipleLocator


# import timedelta
class AverageCalculator:
    def __init__(self,list_of_equips, MAC_ID,critical,area_folder_path):
        try:
            self.mac_id = MAC_ID
            self.list_mac_id_equips_weekly_report = list_of_equips
            self.equipment_list_with_sensor_id = []
            self.critical = critical
            self.area_folder_path = area_folder_path

            logging.info(f"TrendGenerator instance initialized with MAC_ID: {self.mac_id}")
        except Exception as e:
            logging.error("Error in Trend generator class: " + str(e))


    def calculate_average_for_axis(self, sheet_data, axis_name):
        try:
            # Assuming sheet_data has a 'DateTime' column and a 'Value' column
            sheet_data['DateTime'] = pd.to_datetime(sheet_data['DateTime'], format='%d/%m/%Y %I:%M %p')

            # Extract the correct axis name from the provided axis_name
            extracted_axis = axis_name.split('_')[-1]

            # Calculate the average for the 'Value' column
            if not sheet_data.empty:
                average_value = sheet_data['Value'].dropna().mean()
                #print(average_value, '/////////////////////////////')
                result_data = pd.DataFrame({'Axis': [extracted_axis], 'Average_Value': [average_value]})
                #print(result_data,'resultdataaaaaaaaaaaa line 37')
            else:
                logging.info(f"No data available for the specified time range for axis {extracted_axis}.")
                result_data = pd.DataFrame(columns=['Axis', 'Average_Value'])

            return result_data

        except Exception as e:
            logging.error(f"Error in calculate_average_for_axis: {e}")
            return pd.DataFrame(columns=['Axis', 'Average_Value'])

    # def calculate_average_axis_wise(self, mac_id):
    #     try:
    #         excel_file_path = f'C:/Vegam/Trends_alert/outputs/vrms_data_{mac_id}.xlsx'
    #         df = pd.read_excel(excel_file_path, sheet_name=None)
    #
    #         # Calculate average separately for each axis
    #         averages = {'MAC_ID': mac_id}
    #         for sheet_name, sheet_data in df.items():
    #             if mac_id in sheet_name and '_' in sheet_name:
    #                 _, _, axis,_ = sheet_name.rsplit('_', 3)  # Extract axis from sheet name
    #                 #print(f"Sheet Name: {sheet_name}, Extracted Axis: {axis},macid:{mac_id}")
    #                 averages[axis] = self.calculate_average_for_axis(sheet_data, axis)['Average_Value'].mean()
    #                 logging.info(f"Successfully calculated average for axis: {axis}")
    #
    #         return averages
    #
    #     except Exception as e:
    #         logging.error(f"Error in calculate_average_axis_wise: {e}")

    def calculate_percentage_beyond_critical(self, sheet_data, axis_name,mac_id):
        try:
            # Assuming sheet_data has a 'DateTime' column and a 'Value' column
            sheet_data['DateTime'] = pd.to_datetime(sheet_data['DateTime'], format='%d/%m/%Y %I:%M %p')
            critical = self.critical

            # Extract the correct axis name from the provided axis_name
            extracted_axis = axis_name.split('_')[-1]

            # Calculate the percentage beyond critical for the 'Value' column
            count_beyond_critical = sheet_data[sheet_data['Value'] > critical].shape[0]
            print(count_beyond_critical,'count_beyond_critical')
            total_rows = sheet_data.shape[0]
            print(total_rows,'totalrows')

            if total_rows > 0:
                percentage_beyond_critical = round((count_beyond_critical / total_rows) * 100, 2)
                print(percentage_beyond_critical, 'percentage_beyond_critical')

                print(percentage_beyond_critical,'percentage_beyond_criticalpercentage_beyond_criticalpercentage_beyond_criticalpercentage_beyond_critical')
            else:
                percentage_beyond_critical = 0

            return percentage_beyond_critical

        except Exception as e:
            import traceback
            print(f'error in calc_perc:{e}')
            traceback.print_exc()

            logging.error(f"Error in calculate_percentage_beyond_critical: {e}")

            return 0  # Return 0 in case of an error or empty data

    def calculate_average_axis_wise(self, mac_id):
        try:
            # excel_file_path = f'C:/Vegam/Trends_alert/outputs/vrms_data_{mac_id}.xlsx'
            excel_file_path = os.path.join(self.area_folder_path, f'vrms_data_{mac_id}.xlsx')

            df = pd.read_excel(excel_file_path, sheet_name=None)

            # Calculate average separately for each axis
            averages = {'MAC_ID': mac_id}
            for sheet_name, sheet_data in df.items():
                if mac_id in sheet_name and '_' in sheet_name:
                    _, _, axis, _ = sheet_name.rsplit('_', 3)  # Extract axis from sheet name
                    avg_value = self.calculate_average_for_axis(sheet_data, axis)['Average_Value'].mean()
                    # Calculate percentage beyond critical for the current axis
                    rounded_avg_value = round(avg_value, 2)  # Round to 2 decimal points
                    averages[axis] = rounded_avg_value

                    percentage_beyond_critical = self.calculate_percentage_beyond_critical(sheet_data, axis, mac_id)
                    averages[f'{axis}_Percentage_Beyond_Critical'] = percentage_beyond_critical
                    logging.info(f"Successfully calculated average for axis: {axis}")

            return averages

        except Exception as e:
            logging.error(f"Error in calculate_average_axis_wise: {e}")

    # def get_equipmentid(self, mac_id):
    #     combined_equipment_sensor_ids = self.list_mac_id_equips_weekly_report if len(
    #         self.list_mac_id_equips_weekly_report) != 0 else "no data"
    #
    #     df = pd.DataFrame({'EquipmentID_Sensor_ID': combined_equipment_sensor_ids})
    #     equip_details_df = df[['EquipmentID_Sensor_ID']]
    #     #print(self.list_mac_id_equips_weekly_report,'equip_details_df')
    #     self.equipment_list_with_sensor_id = equip_details_df['EquipmentID_Sensor_ID'].tolist()
    #     #print(self.equipment_list_with_sensor_id,'self.equipment_list_with_sensor_id')
    #
    #     result = {'MAC_ID': mac_id, 'Equipment ID': None,
    #               'Velocity RMS - Radial Horizontal': None,
    #               'Velocity RMS - Radial Vertical': None,
    #               'Velocity RMS - Axial': None}  # Initialize with default values
    #
    #     for equip, equipment_id in enumerate(self.equipment_list_with_sensor_id):
    #         #print(equipment_id,'equipmentidddddddddddddddddddddddddd')
    #         averages = self.calculate_average_axis_wise(mac_id)
    #         #if mac_id ==
    #         #print(equip,'equipmmmmskdjfhbvsjkh')
    #         result.update({'Equipment ID': equipment_id,
    #                        'MAC_ID':averages.get('MAC_ID'),
    #                        'Velocity RMS - Radial Horizontal': averages.get('X'),
    #                        'Velocity RMS - Radial Vertical': averages.get('Y'),
    #                        'Velocity RMS - Axial': averages.get('Z')})
    #         print(result,'result line 92 trendgen')
    #
    #     return result
