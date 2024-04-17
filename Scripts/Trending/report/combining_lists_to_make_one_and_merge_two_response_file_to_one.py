'''
OBJECTIVE : #MONTHLY
Once we have 2 files of responses, it will merge and make one response,  if responses are separated in files then it
will make one otherwise if two files are present with right responses, then it will prepare one response and store in a
text file.

'''



import ast
import os
import json

print("spaceceeeeeee")
input_folder = "C://Vegam//processed_data_text_format"
second_api_folder = "C://Vegam//merged_json_response_21_01"
output_folder = "C://Vegam//merging_0122_2201"

# Function to process each text file
def process_text_file(file_path, output_folder):
    try:
        print(f"Combining started for - {file_path}")
        with open(file_path, 'r') as file:
            lines = file.readlines()
            data_string = lines[0]
            line_json_inv = json.loads(data_string)
            line_json = json.loads(line_json_inv)

            # Assuming the data is stored in the first (and only) line
            # Remove the leading and trailing single quotes
            combined_list = []
            combined_list.append(line_json)
            directory, base_filename = os.path.split(file_path)
            base_filename, extension = os.path.splitext(base_filename)

            # Insert "2131" before the base filename
            new_base_filename = "2131_" + base_filename.rsplit("_", 1)[0]

            # Join the components back together to form the new filename
            filename = os.path.join(new_base_filename + extension)
            for root, dirs, files in os.walk(second_api_folder):
                # Check if the file is in the list of files
                if filename in files:
                    # If found, construct the full path to the file
                    file_path = os.path.join(root, filename)
                    # Open the file and read its contents
                    with open(file_path, 'r') as file:
                        # Read each line of the file and append it to the list
                        line = file.readlines()
                        line_str = line[0]
                        line_json = ast.literal_eval(line_str)
                        combined_list.append(line_json)

            for inner_list in combined_list:
                # Iterate through each dictionary in the inner list
                for dictionary in inner_list:
                    # Check if "historical_data" key exists in the dictionary
                    if 'historical_data' in dictionary:
                        # Rename the key from "historical_data" to "historicalData"
                        dictionary['historicalData'] = dictionary.pop('historical_data')
                        # Get the historicalData dictionary
                        historical_data = dictionary['historicalData']
                        # Check if "signal_id" key exists in the historicalData dictionary
                        for signalid in historical_data:
                            if 'signal_id' in signalid:
                                # Rename the key from "signal_id" to "signalId"
                                signalid['signalId'] = signalid.pop('signal_id')

            # print(combined_list)
            # for line in lines:
            #     # lst = eval(line)
            #     # response.raise_for_status()
            #     lst = json.loads(line)
            #     combined_list.append(lst)
                # print(combined_list)

        # final_response_list = []
        #
        # for sublist in combined_list:
        #     historical_data = []
        #
        #     for entry in sublist[0]['historicalData']:
        #         signal_id = entry['signalId']
        #         vtq_values = entry['vtq']
        #         historical_data.append({'vtq': vtq_values, 'signal_id': signal_id})
        #
        #     final_response_list.append({'historical_data': historical_data})
        #
        # return final_response_list
        output_list = []

        historical_data = {'historicalData': []}
        for sublist in combined_list:
            for item in sublist:
                for data in item['historicalData']:
                    signal_id = data['signalId']
                    vtq_list = data['vtq']
                    # Check if the signal ID already exists in the output list
                    signal_id_exists = False
                    for existing_data in historical_data['historicalData']:
                        if existing_data['signalId'] == signal_id:
                            existing_data['vtq'].extend(vtq_list)  # Append VTQ values to existing signal ID
                            signal_id_exists = True
                            break
                    if not signal_id_exists:
                        # If signal ID doesn't exist, create a new dictionary
                        historical_data_item = {'signalId': signal_id, 'vtq': vtq_list}
                        historical_data['historicalData'].append(historical_data_item)
            if historical_data not in output_list:
                output_list.append(historical_data)

        output_list[-1].update({'fromTime': combined_list[0][0]['fromTime'], 'toTime': combined_list[-1][0]['toTime'], 'byMin': False})
        # print(output_list)
        output_list_txt = json.dumps(output_list)
        return output_list_txt
    except Exception as ex:
        print(f"Error in func as {ex}")

try:
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Iterate over all text files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith('.txt'):
            input_file_path = os.path.join(input_folder, filename)
            # Process each text file
            processed_data = process_text_file(input_file_path, second_api_folder)
            # Save the processed data to a new file in the output folder
            output_file_path = os.path.join(output_folder, os.path.splitext(filename)[0] + '_0131.txt')
            with open(output_file_path, 'w') as output_file:
                json.dump(processed_data, output_file, indent=4)
            print("Processed data saved to:", output_file_path)
except Exception as ex:
    print(f"Error as {ex}")
