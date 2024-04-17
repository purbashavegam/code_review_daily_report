import time
from itertools import islice
import pandas as pd
# import logger
from Scripts.Trending.report.logger_file import logger

class Util_Data():
    def __init__(self, json_data, area_name):
        try:
            self.json_config = json_data
            self.current_area = area_name
        except Exception as ex:
            logger.error(f"Error in Util Class initialization {ex}")

    def intermediate_excels_save_sensor_wise(self, excel_file, combined_dict):
        try:
            with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
                for key, df in combined_dict.items():
                    df.to_excel(writer, sheet_name=key, index=False)
                    time.sleep(2)

            time.sleep(3)
            logger.info(f"Excel creation Done for {excel_file}")
        except Exception as ex:
            logger.error(f"Error in excel preparation {ex}")

    def machine_on_off_calculation(self, combined_dict, output_intermediate_excel_file):
        try:
            # print(self.json_config["util_json_data"])
            # print(self.json_config["util_json_data"]["on_off_threshold_level_area_wise"])
            threshold_level_for_cur_area = float(self.json_config["util_json_data"]["on_off_threshold_level_area_wise"][self.current_area])
            dfs = combined_dict
            excel_file = output_intermediate_excel_file
            if len(dfs):
                # print(dfs)
                # print(type(dfs))
                sheet_names = list(dfs.keys())
                # print(sheet_names)
                # self.intermediate_excels_save_sensor_wise(f"C://Vegam//Trends_alert//report//daily//18_03_2024//check//{sheet_names[0]}.xlsx", dfs)

                sheet_names = [name for name in sheet_names if not name.endswith('Temp')]
                sheet_names_prefix_remove = [prefix_.split('_', 2)[-1] for prefix_ in sheet_names]

                # min_length = min(len(df) for df in dfs.values())
                min_length = min(len(df) for df in islice(dfs.values(), 3))

                # Trim excess rows from DataFrames with more rows
                for key, df in islice(dfs.items(), 3):
                    if len(df) > min_length:
                        dfs[key] = df.iloc[:min_length]


                datetime_check = all(dfs[sheet].DateTime.equals(dfs[list(dfs.keys())[0]].DateTime) for sheet in dfs.keys())

                if datetime_check:
                    for sheet_name, df in list(dfs.items())[:3]:
                        dfs[sheet_name] = df.rename(columns={'Value': sheet_name})
                    combined_df = pd.concat([df.set_index('DateTime') for df in dfs.values()], axis=1, join='outer')
                    # combined_df = combined_df.drop(columns=['Value'])
                    combined_df = combined_df.reset_index()
                else:
                    logger.critical("DateTime values are not the same across all sheets.")

                    # all_datetimes = pd.concat([df.DateTime for df in dfs.values()]).unique()

                    dfs = {k: v for k, v in dfs.items() if not k.endswith('Temp')}
                    for sheet_name, df in dfs.items():
                        unique_datetimes = df.DateTime.unique()
                        other_sheets = {other_sheet: other_df for other_sheet, other_df in dfs.items() if
                                        other_sheet != sheet_name}

                        for other_sheet_name, other_df in other_sheets.items():
                            # Convert DateTime column to datetime type
                            # other_df['DateTime'] = pd.to_datetime(other_df['DateTime'])

                            # Find cells where DateTime values are different
                            diff_cells = []
                            for index, row in df.iterrows():
                                value_sheet = row['DateTime']
                                value_other_sheet = other_df.iloc[index]['DateTime']
                                if value_sheet != value_other_sheet:
                                    diff_cells.append((sheet_name, index, value_sheet, value_other_sheet))

                            # Process diff_cells as needed
                            if diff_cells:
                                for diff_cell in diff_cells:
                                    unmatched_index = diff_cell[1]
                                    unmatched_dt = diff_cell[2]
                                    unmatched_dt_datetime = pd.to_datetime(unmatched_dt, dayfirst=True)
                                    other_dt_datetime = pd.to_datetime(other_df.at[unmatched_index, 'DateTime'],
                                                                       dayfirst=True)
                                    if unmatched_index in other_df.index:
                                        if other_dt_datetime > (
                                                unmatched_dt_datetime + pd.Timedelta(seconds=5)) or \
                                                other_dt_datetime > (
                                                unmatched_dt_datetime - pd.Timedelta(seconds=5)):
                                            existing_value = other_df.at[unmatched_index, other_df.columns[1]]
                                            other_df.at[unmatched_index, 'DateTime'] = unmatched_dt
                                            other_df.at[unmatched_index, other_df.columns[1]] = existing_value

                                # Restore DateTime column to string format
                                # other_df['DateTime'] = other_df['DateTime'].dt.strftime('%m/%d/%Y %H:%M:%S')
                                dfs[other_sheet_name] = other_df
                        else:
                            logger.critical(
                                f"Check the data in dataframe, unmatched flag is false but not identifying the unmatched data in {sheet_name}")
                    for sheet_name, df in list(dfs.items())[:3]:
                        dfs[sheet_name] = df.rename(columns={'Value': sheet_name})

                    # print(dfs.values())
                    combined_df = pd.concat([df.set_index('DateTime') for df in dfs.values()], axis=1, join='outer')
                    # combined_df = combined_df.drop(columns=['Value'])

                    combined_df = combined_df.reset_index()

                # print(combined_df)

                machine_off_df = combined_df[(pd.to_numeric(combined_df[sheet_names[0]], errors='coerce') < threshold_level_for_cur_area) |
                                             (pd.to_numeric(combined_df[sheet_names[1]], errors='coerce') < threshold_level_for_cur_area) |
                                             (pd.to_numeric(combined_df[sheet_names[2]], errors='coerce') < threshold_level_for_cur_area)]

                # print(machine_off_df)

                indices_to_remove = machine_off_df.index

                machine_on_df = combined_df.copy()
                machine_on_df = machine_on_df.drop(indices_to_remove)

                # print(machine_on_df)
                # print(len(machine_on_df))

                column_value_x = sheet_names[0]
                column_df_x = machine_on_df[['DateTime', column_value_x]].copy()
                column_df_x.rename(columns={column_value_x: 'Value'})
                # df_x.columns = ['DateTime', remove_prefix(sheet_names[0])]

                column_value_y = sheet_names[1]
                column_df_y = machine_on_df[['DateTime', column_value_y]].copy()
                column_df_y.rename(columns={column_value_y: 'Value'})
                # df_y.columns = ['DateTime', remove_prefix(sheet_names[1])]

                column_value_z = sheet_names[2]
                column_df_z = machine_on_df[['DateTime', column_value_z]].copy()
                column_df_z.rename(columns={column_value_z: 'Value'})
                # df_z.columns = ['DateTime', remove_prefix(sheet_names[2])]

                combined_dict[sheet_names_prefix_remove[0]] = column_df_x
                combined_dict[sheet_names_prefix_remove[1]] = column_df_y
                combined_dict[sheet_names_prefix_remove[2]] = column_df_z
                # print(len(combined_dict))
                # print(combined_dict.keys())

                for key_name in sheet_names_prefix_remove:
                    if key_name in combined_dict.keys():
                        combined_dict[key_name] = combined_dict[key_name].rename(columns={f'C_VRMS_{key_name}': 'Value'})
                        combined_dict[key_name]['DateTime'] = pd.to_datetime(combined_dict[key_name]['DateTime'],
                                                                             dayfirst=True).dt.strftime(
                            "%d/%m/%Y %H:%M %p")
                for key_name_, df_ in combined_dict.items():
                    if key_name_.endswith('Temp'):
                        combined_dict[key_name_]['DateTime'] = pd.to_datetime(df_['DateTime'], dayfirst=True).dt.strftime(
                            "%d/%m/%Y %H:%M %p")

                # print(combined_dict.keys())
                self.intermediate_excels_save_sensor_wise(excel_file, combined_dict)
            else:
                logger.critical("Data not available in the dictionary, not even any dataframe present")
        except Exception as ex:
            logger.error(f"Error in machine on-off calculation - {ex}")


# if __name__ == "__main__":
#     excel_file = "C://Vegam//Trends_alert//report//daily//15_03_2024//check//C_VRMS_F6A484F0CBF6_1113_X_Axis.xlsx"
#     output_intermediate_excel_file = "C://Vegam//Trends_alert//report//daily//11_03_2024//Compressor House//vrms_copy2_C258249CFE98.xlsx"
#     dfs = pd.read_excel(excel_file, sheet_name=None)
#     call_func = Util_Data()
#     call_func.machine_on_off_calculation(dfs, output_intermediate_excel_file)








