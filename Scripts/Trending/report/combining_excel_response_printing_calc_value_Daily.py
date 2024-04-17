'''
OBJECTIVE : #DAILY
This file is required in case for combining the two time interval excels of VRMS values, and calculate those values and
show us the average and percentages by printing.

'''


import os
import pandas as pd

# Define critical value
critical_value = 10

# Function to process Excel files with the same name
def process_excel_files(folder_paths):
    results = {}
    for folder_path in folder_paths:
        for filename in os.listdir(folder_path):
            if filename.endswith(".xlsx"):
                file_path = os.path.join(folder_path, filename)
                excel = pd.ExcelFile(file_path)
                sheet_names = excel.sheet_names
                for sheet_name in sheet_names:
                    df = excel.parse(sheet_name)
                    results.setdefault(filename, {}).setdefault(sheet_name, []).append(df)

    return results

# Folder paths containing Excel files
folder_paths = [
    "C://Vegam//Trends_alert//report//22_03_2024_evening//Compressor House",
    "C://Vegam//Trends_alert//report//22_03_2024_morning//Compressor House"
]

# Process Excel files
results = process_excel_files(folder_paths)

# Calculate the average and percentage for each sheet in each merged dataframe
final_results = {}
for filename, sheet_data in results.items():
    for sheet_name, dfs_list in sheet_data.items():
        merged_df = pd.concat(dfs_list, ignore_index=True)
        last_three_dataframes = merged_df.tail(3)
        total_rows = len(merged_df)
        if 'Value' in merged_df.columns:
            total_rows_more_than_critical = len(merged_df[merged_df['Value'] > critical_value])
            if total_rows == 0:
                percentage_more_than_critical = 0.0
                avg_value = 0.0
            else:
                percentage_more_than_critical = (total_rows_more_than_critical / total_rows) * 100
                avg_value = merged_df["Value"].mean()
        else:
            percentage_more_than_critical = 0.0
            avg_value = 0.0

        final_results.setdefault(filename, {}).setdefault(sheet_name, {'average_value': avg_value, 'percentage_more_than_critical': percentage_more_than_critical})

# Print the results

# final_results = {key: final_results[key] for key in list(final_results.keys())[3:]}
for filename, sheet_data in final_results.items():
    print(" ")
    print(f"Excel File: {filename}")
    sheet_data = {key: sheet_data[key] for key in list(sheet_data.keys())[3:]}
    for sheet_name, values in sheet_data.items():
        print(f"  Sheet: {sheet_name}")
        print(f"    Average Value: {values['average_value']}, Percentage Value: {values['percentage_more_than_critical']:.2f}%")






