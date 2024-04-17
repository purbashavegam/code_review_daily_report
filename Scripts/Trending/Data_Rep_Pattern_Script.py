import pandas as pd
import json
from datetime import datetime, timedelta

# import logging

# Step 1: Load Configuration
def load_config(file_path):
    try:
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
        return data
        # logger.info(f"reading json file '{file_path}'")
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        # logger.info(f"File '{file_path}' not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in '{file_path}': {e}")
        # logger.error(f"Error decoding JSON in '{file_path}': {e}")
        return None

def generate_simulation_data(sheet_name, config):
    try:
        similar_sheet_data = []
        # scenario_sheet_wise = []
        # Specify the Excel file path
        for ele in range(len(config['data_order'])):
            order = config['data_order'][ele]
            proportion = config['data_proportions_burstwise'][str(order)]
            file_path = config['data_Input_folder']+'\\'+config['input_data_files'][str(order)] 
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            if len(df) < proportion:
                total_rows_to_replicate = proportion - (len(df))
                # remaining_rows =  (total_rows) - (total_proportion*num_repetitions)
                num_replications =  int(total_rows_to_replicate/len(df))
                if num_replications == 1:
                    
                    proportion_data = pd.concat([df]* num_replications, ignore_index=True)
                    # proportion_data = proportion_data[:config['data_proportions_burstwise'][str(order)]]
                    # similar_sheet_data.append(proportion_data)
                    if len(proportion_data) < proportion:
                        remaining_rows = proportion - (len(proportion_data))
                        remaining_data = proportion_data[:int(remaining_rows)]
                        if len(remaining_data) < proportion:
                            rows = remaining_rows - len(remaining_data)
                            data = remaining_data[:int(rows)]
                            prop_data = pd.concat([proportion_data, remaining_data, data], ignore_index=True)
                            similar_sheet_data.append(prop_data)
                    else:
                        prop_data = similar_sheet_data[:int(proportion)]
                        similar_sheet_data.append(prop_data)
                elif num_replications == 0:
                    
                    proportion_data = df
                    # proportion_data = proportion_data[:config['data_proportions_burstwise'][str(order)]]
                    # similar_sheet_data.append(proportion_data)
                    if len(proportion_data) < proportion:
                        remaining_rows = proportion - (len(proportion_data))
                        remaining_data = proportion_data[:int(remaining_rows)]
                        prop_data = pd.concat([df, remaining_data], ignore_index=True)
                        similar_sheet_data.append(prop_data)

                    else:
                        prop_data = similar_sheet_data[:int(proportion)]
                        similar_sheet_data.append(prop_data)
                else:
                    proportion_data = pd.concat([df]* num_replications, ignore_index=True)
                    one_day_data = pd.concat([df, proportion_data], ignore_index=True)
                    similar_sheet_data.append(one_day_data)
            else:
                proportion_data = df[:proportion]
                similar_sheet_data.append(proportion_data)
        sheetwise_data = pd.concat(similar_sheet_data)
        return sheetwise_data
    except FileNotFoundError:
        return None

def generate_date_times_with_ampm(start_date_str, num_days, burst_interval):
    try:
        # Convert the input date string to a datetime object
        start_date = datetime.strptime(start_date_str, "%d/%m/%Y %I:%M %p")

        # Create an empty list to store the generated date and time values
        date_times = []

        # Generate date and time values at 20-minute intervals for the specified number of days
        for day in range(num_days):
            for minute in range(0, 1440, burst_interval):  # 1440 minutes in a day
                new_date = start_date + timedelta(days=day, minutes=minute)
                date_times.append(new_date.strftime("%d/%m/%Y %I:%M %p"))

        return date_times
    except ValueError as e:
        return str(e)

def append_alternate_rows(dataframes):
    combined_rows = []
    # max_rows = max(dataframes.shape[0])
    max_rows = 48

    for i in range(max_rows):
        for df in dataframes:
            # if i < df.shape[0]:
            if i < 48:
                combined_rows.append(df.iloc[i])
    
    combined_df = pd.concat(combined_rows, axis=1).transpose()
    return combined_df

def save_simulated_data(config):
    try:
        start_date_str = config['start_date']
        num_days = config['simulation_duration_in_days']
        burst_interval = int(1440/config['no_of_burst_per_day'])
        
        date_times = generate_date_times_with_ampm(start_date_str, num_days, burst_interval)
        
        sheet_names = ['Series_1', 'Series_2', 'Series_3']
        all_data = []
        # scenario = []
        for sheet_name in sheet_names:
            dataframe = generate_simulation_data(sheet_name, config)
            # scenario_data = append_alternate_rows(dataframe)
            # scenario.append(scenario_data)
            all_data.append(dataframe)
        import datetime
        file_name = config['input_data_files']['1']
        time_date = datetime.datetime.now()
        formatted_datetime = time_date.strftime("%Y_%m_%d %H_%M_%S")
        output_file_path = config['data_Output_folder']+'\\'+config['output_file_name']+'_'+formatted_datetime+'_'+file_name[-8:-4]+'.xlsx'
        with pd.ExcelWriter(output_file_path) as writer:
            
            for i in range(len(all_data)):
                total_proportion = int(sum(config['data_proportions_burstwise'].values()))
                total_rows = int(config['no_of_burst_per_day']*config['simulation_duration_in_days'])
                num_repetitions = int(total_rows/total_proportion)

                simulation_data = pd.concat([all_data[i]] * num_repetitions, ignore_index=True)
                # Add any remaining rows to match the exact number of rows
                remaining_rows =  (total_rows) - (total_proportion*num_repetitions)
                if remaining_rows > 0:
                    simulation_data = pd.concat([simulation_data, all_data[i].head(remaining_rows)], ignore_index=True)
                    simulation_data['DateTime'] = date_times
                # return repeated_df
                    simulation_data.to_excel(writer, sheet_name=f"{sheet_names[i]}", index=False)
                    
                else:
                    simulation_data['DateTime'] = date_times
                    simulation_data.to_excel(writer, sheet_name=f"{sheet_names[i]}", index=False)
                json_data = [config]
                json_summary_data = pd.DataFrame(json_data).T
                json_summary_data.rename(columns = {0:'Configuration'}, inplace = True)
            json_summary_data.to_excel(writer, sheet_name='JSON_Sumarry')
                    
                    
    except FileNotFoundError:
        return None

if __name__ == "__main__":
    config_file = "D:\Code\Trending\Data_Rep_config_file.json"  # Modify this with your config file path
    config = load_config(config_file)
    save_simulated_data(config)


# print(formatted_datetime)
