import json
import os

data = {
        "data_Input_folder": r"D:\Data\JSW_SPEED_DATA",
        "data_Output_folder": r"D:\Data\New_folder_2",
        "output_file_name": "simulated_data",
        "input_data_files": {"1":"JSW_6V__RPM_683.6_EAD9FBF48C8A.xls", "2":"JSW_6V__RPM_1119.4_EAD9FBF48C8A.xls", "3":"JSW_6V__RPM_1533_EAD9FBF48C8A.xls"},
        'no_of_burst_per_day': 48,
        "data_order": [1, 2, 3],
        "data_proportions_burstwise": {
            "1": 48,
            "2": 48, 
            "3": 48
            }, # "2": 96
        "simulation_duration_in_days": 90,
        "start_date": "01/01/2023 12:00 AM"
    }

# Specify the folder path and file name where you want to save the JSON data
folder_path = "D:\Code\Trending"  # Replace with your desired folder path
file_name = "config_file.json"

# Create the full file path by joining the folder path and file name
full_file_path = os.path.join(folder_path, file_name)

# Serialize the data to JSON format and write it to the specified file
with open(full_file_path, "w") as json_file:
    json.dump(data, json_file)

print(f"Generated data saved to {full_file_path}")



