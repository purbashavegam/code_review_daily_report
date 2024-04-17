import os
import json
import pandas as pd
import numpy as np
# import plotly.express as px  # Updated import for Plotly
from scipy.stats import linregress
# import plotly.graph_objects as go
# import multiprocessing
# from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib

matplotlib.use('TkAgg')  # Use the TkAgg backend (or another suitable one)
# import shutil
from scipy.stats import norm
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import dataframe_image as dfi
import datetime
from PIL import Image
from matplotlib.ticker import MaxNLocator
import time

# Record the start time
start_time = time.time()

# Your script or code here

# Function to load, preprocess data and create plots
def preprocess_data(directory_path, output_dir):
    # if dataframes is None:
    dataframes = []  # Initialize the dictionary if it doesn't exist

    folder_name = os.path.basename(directory_path)  # Extract the folder name

    print(f"Processing directory: {directory_path}")

    # Iterate through subdirectories (folder names) and files in the specified directory
    for item, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(item, file)
            item_path = os.path.join(directory_path, item)
           
            # Extract the file name without extension
            file_name = os.path.splitext(os.path.basename(file))[0]

            # # Calculate the relative path based on the current file being processed
            data = item_path + '\\' + file
            df = pd.read_excel(data, sheet_name=None)  # Read all sheets into a dictionary
            for axis_name, sheet_name in [('X_Axis', 'Series_1'), ('Y_Axis', 'Series_2'), ('Z_Axis', 'Series_3')]:
                df_axis = df.get(sheet_name, pd.DataFrame()).copy()  # Create a copy

                # Select the columns you want to keep (e.g., the last two columns)
                columns_to_keep = ['DateTime', 'Value']  # Adjust column names as needed

                # Filter the DataFrame to include only the specified columns
                df_axis = df_axis[columns_to_keep]

                # Convert DateTime column to datetime format
                df_axis['DateTime'] = pd.to_datetime(df_axis['DateTime'], format='%d/%m/%Y %I:%M %p')
                # Store the DataFrame in the dictionary with its name
                dataframe_name = f'{folder_name}_{file_name}_{axis_name}'.replace('.xls', '')
                dataframes.append((file_name, item_path, axis_name, df_axis))

                # print(f'Generated dataframe name: {dataframe_name}')
        
    return dataframes

def regression_metrics_dataframe(y_true, y_pred, col_name):
    """
    Calculate multiple regression evaluation metrics and return them as a DataFrame.

    Parameters:
    - y_true: array-like
        Ground truth target values.
    - y_pred: array-like
        Predicted target values.

    Returns:
    - pd.DataFrame
        A DataFrame containing the calculated metrics: MSE, MAE, RMSE, MAPE, and R².
    """
    metrics = {
        'MSE': mean_squared_error(y_true, y_pred),
        'MAE': mean_absolute_error(y_true, y_pred),
        'RMSE': np.sqrt(mean_squared_error(y_true, y_pred)),
        # 'MAPE': np.mean(np.abs((y_true - y_pred) / y_true)) * 100,
        'R-squared': r2_score(y_true, y_pred)
    }

    metrics_df = pd.DataFrame.from_dict(metrics, orient='index', columns=[col_name])
    return metrics_df

def raw_data_plot(df, directory_axis, dataframe_name, axis_name, data_duration_days):
    
    plt.figure(figsize=(12, 6))
    chart_name = f'Original_Data_{dataframe_name}_{axis_name} - {data_duration_days} days'
    
    # # Plot the data using Seaborn
    # plt.plot(df['DateTime'], df['Value'], label='Original Data')
    # plt.xlabel('Date and Time')
    # plt.ylabel('Velocity mm/sec')
    # plt.title(chart_name)
    # plt.legend()
    
    # # Save the individual chart as an image in the specified output format
    # output_file = os.path.join(directory_axis, f'2.{chart_name}.{config["output_format"]}')
    # plt.savefig(output_file, format=config['output_format'])
    # plt.close()

def moving_average_trend(df, window_sizes):
    result_df = df.copy()

    for window_size in window_sizes:
        
        # Calculate the moving average
        result_df[f'MovingAverage_{window_size}'] = df['Value'].rolling(window=window_size).mean()
        result_df.loc[:window_size - 1, f'MovingAverage_{window_size}'] = df.loc[:window_size - 1, 'Value']  # pm

    return result_df

def moving_average_plot(dataframe, dataframe_name, df_name, config, directory_axis, data_duration_days):

    trending_methods = config['trending_methods']      

    ma_metrics = []
    for method in trending_methods:
    
        if method['enabled'] and method['name'] == 'Moving Average':
            window_sizes = method['window_sizes']
            
            colors = ['red', 'green']
            # plt.figure(figsize=(12, 6))
            moving_average_dfs = {}
            
            # Calculate moving averages for each window size
            for window_size, color in zip(window_sizes, colors):
                result_df = moving_average_trend(dataframe.copy(), [window_size])
                result_df.fillna(0)
                moving_average_dfs[window_size] = result_df  # Store the result_df in the moving_average_dfs dictionary
                
                column_name = list(result_df.columns)
                metrics_df_name = dataframe_name+'_'+'Moving_Average_'+str(window_size)+'_'+df_name
                Moving_Average_evl_result = regression_metrics_dataframe(result_df['Value'], result_df[str(column_name[2])], metrics_df_name)
                ma_metrics.append(Moving_Average_evl_result)

                # chart_name = f'{dataframe_name}_{df_name}_Moving_Average_{window_size} - {data_duration_days} days'
                # y_column_name = f'MovingAverage_{window_size}'
                
                # # Plot the data                
                # plt.plot(result_df['DateTime'][window_size:], result_df[y_column_name][window_size:], color=color, label=f'Moving Average (Window {window_size})')
                # plt.xlabel('Date and Time')
                # plt.ylabel('Moving Average')
                # plt.title(chart_name)
                # plt.legend()
    
                # # Save the individual chart as an image in the specified output format
                # output_file = os.path.join(directory_axis, f'3.{chart_name}.{config["output_format"]}')
                # plt.savefig(output_file, format=config['output_format'])
                # plt.close()

    return ma_metrics

def polynomial_trend(dataframe, dataframe_name, df_name, config, directory_axis, data_duration_days):
    trending_methods = config['trending_methods']      

    # Calculate the duration of data in number of days
    df = dataframe
    start_date = pd.to_datetime(df['DateTime'].min())
    end_date = pd.to_datetime(df['DateTime'].max())
    data_duration_days = ((end_date - start_date).days) + 1
    poly_metrics = []
    for method in trending_methods:
        if method['enabled'] and method['name'] == 'Polynomial Trendline':
            degrees = method['degrees']
            colors = ['red', 'green']
            polynomial_trend_dfs = {}
            
            # plt.figure(figsize=(12, 6))
            # Calculate polynomial trendlines for each degree
            for degree, color in zip(degrees, colors):
    
                x = np.arange(len(df))
                y = df['Value']
                # Fit a polynomial of the specified degree
                coefficients = np.polyfit(x, y, degree)
                polynomial = np.poly1d(coefficients)
                y=polynomial(x)
                polynomial_trend_dfs[degree] = y
                
                Poly_evaluation_result = regression_metrics_dataframe(dataframe['Value'], 
                                                                      pd.Series(y), dataframe_name+'_'+'ploy_degree_'+str(degree)+'_'+df_name)                             
                poly_metrics.append(Poly_evaluation_result)
            #     # print('Polynomial Data')
            #     plt.plot(dataframe['DateTime'], y, color=color, label=f'Polynomial Trendline (Degree {degree})')
            # plt.xlabel('Date and Time')
            # plt.ylabel('Value')
            # plt.title(f'{dataframe_name} Polynomial Trendline (Degree_ {degree}) - {data_duration_days} days')
            # plt.legend()
            
            # # # Save the trendline chart as an image in the specified output format
            # # trendline_output_file = os.path.join(directory_axis, f'{dataframe_name}_Polynomial_Trendline_Degree_{degree}.{config["output_format"]}')
            # # plt.savefig(trendline_output_file, format=config['output_format'])
            
            # # Close the plot to release resources (optional)
            # plt.close()


    return poly_metrics

def exponential_moving_average(data, alpha):
    ema = data.copy()
    ema['EMA'] = data['Value'].ewm(alpha=alpha, adjust=False).mean()
    return ema

def exp_moving_avg_plot(dataframe, directory_axis, dataframe_name, df_name, config, data_duration_days):
    # Add code to save EMA plots similar to how you save other plots
    trending_methods = config['trending_methods']
    ema_metrics = []
    
    # # Create a new figure and axis
    # plt.figure(figsize=(12, 6))
    # Iterate through the saved exponential moving average (EMA) dataframes and generate plots
    for method in trending_methods:
        if method['name'] == 'Exponential Moving Average':
            ema_dfs = []
            if 'alpha' in method:  # Check if 'alpha' is defined in the method
                alpha = method['alpha']  # Get the alpha value from the config
                result_df = exponential_moving_average(dataframe.copy(), alpha)
                ema_dfs.append(result_df)
                EMA_evaluation_result = regression_metrics_dataframe(result_df['Value'], result_df['EMA'],
                                                                     dataframe_name+'_'+'EMA_' + df_name)
                ema_metrics.append(EMA_evaluation_result)

            for i, result_df in enumerate(ema_dfs):
                # days_in_duration = len(result_df)/48
                alpha = \
                    [method['alpha'] for method in trending_methods if method['name'] == 'Exponential Moving Average'][
                        0]
                # # Use the correct index for trending_methods
                # chart_name = f'{dataframe_name}_EMA_alpha_{alpha}_{df_name}_{data_duration_days} days'
                # y_column_name = 'EMA'

                # # Plot the data 
                # plt.plot(result_df['DateTime'], result_df[y_column_name], label=f'EMA (Alpha {alpha})')
                # plt.xlabel('Date and Time')
                # plt.ylabel('EMA')
                # plt.title(chart_name)
                # plt.legend()

                # # Save the individual EMA chart as an image in the specified output format
                # ema_output_file = os.path.join(directory_axis, f'4.{chart_name}.{config["output_format"]}')
                # plt.savefig(ema_output_file, format=config['output_format'])

                # # Close the plot to release resources (optional)
                # plt.close()
    # return ema_metrics
    return ema_metrics

def trend_line_method(df):
    x = df['DateTime'].astype(np.int64) // 10 ** 9  # Convert to Unix timestamp (seconds)
    slope, intercept, _, _, _ = linregress(x, df['Value'])
    trendline = intercept + slope * x

    return trendline, slope

def TrendLine_Method(original_df, dataframe_name, df_name, output_folder, config, data_duration_days):
    trending_methods = config['trending_methods']
    trl_metrics = []
    
    # # Create a new figure and axis for the original data plot
    # plt.figure(figsize=(12, 6))
    # data = original_df[-336:]
    # Iterate through the saved exponential moving average (EMA) dataframes and generate plots
    for method in trending_methods:
        if method['enabled'] and method['name'] == 'Trend Line':
            # data_duration_days = len(original_df)/48
            # Now, apply the trendline method to the original DataFrame
            trendline, slope = trend_line_method(original_df)
            # print('Trend Line Data')

            original_df['Trendline'] = trendline
            metrics_df_name = dataframe_name+'_'+'Trend_Line_' + df_name
            # original_df = original_df[-336:]
            TRL_evaluation_result = regression_metrics_dataframe(original_df['Value'], trendline,
                                                                 dataframe_name+'_'+'Trend_Line_' + df_name)
            TRL_evaluation_result.at['Slope', metrics_df_name] = slope

            trl_metrics.append(TRL_evaluation_result)
            

            # # Plot 
            # plt.plot(original_df['DateTime'], original_df['Trendline'], 'r', label='Trendline')
            # plt.xlabel('Date and Time')
            # plt.ylabel('Value')
            # plt.title(f'{dataframe_name} Trendline_{df_name} - {data_duration_days} days')
            # plt.legend()

            # # # Save the combined chart as an image in the specified output format
            # # trendline_output_file = os.path.join(output_folder, f'{dataframe_name}_Trendline.{config["output_format"]}')
            # # plt.savefig(trendline_output_file, format=config['output_format'])

            # # Close the plot to release resources (optional)
            # plt.close()

            # # print(f'Individual and combined plots, along with trendline, generated for {dataframe_name}')

    return trl_metrics

def Trend_line_parreto_chart(original_df, dataframe_name, df_name, output_folder, 
                             config, data_duration_days, days_to_consider, burst_per_day):
    step_size = burst_per_day
    chunk_size = burst_per_day*days_to_consider
    
    trl_metrics = []
    sub_dataframes = []
    
    count = 0

    for start_row in range(0, len(original_df), step_size):
        end_row = start_row + chunk_size
        # print(start_row, end_row, "st row, en row")
        if end_row >= len(original_df):     
            end_row = len(original_df)
            count = count+1
        if count == 1 or count ==0:

            sub_df = original_df[start_row:end_row]
            sub_dataframes.append(sub_df)
            size = len(sub_dataframes)+1
            trendline, slope = trend_line_method(sub_df)
            sub_df['Trendline'] = trendline
            metrics_df_name = dataframe_name[:-5]+'_'+str(size)+'_day'
            # original_df = original_df[-336:]
            TRL_evaluation_result = regression_metrics_dataframe(sub_df['Value'], trendline,
                                                                 metrics_df_name)
            TRL_evaluation_result.at['Vrms Trend rate', metrics_df_name] = slope
            trl_metrics.append(TRL_evaluation_result.T)

    print(trl_metrics)
    return trl_metrics

def format_y_ticks(value, pos): #format the y-axis labels
    if value >= 1:
        return f'{int(value):,d}'
    else:
        return f'{value:.6f}'

# def axis_name_for_report(axis_name):
#     if 'X_Axis' == axis_name:
#         axis_name = 'Radial_Horizontal'
#     elif 'Y_Axis' == axis_name:
#         axis_name = 'Axial'
#     elif 'Z_Axis' == axis_name:
#         axis_name = 'Radial_Vertical'
#     return axis_name
        
def axis_name_for_report(axis_name):
    if 'X_Axis' == axis_name:
        axis_name = 'Axial'
    elif 'Y_Axis' == axis_name:
        axis_name = 'Radial_Vertical'
    elif 'Z_Axis' == axis_name:
        axis_name = 'Radial_Horizontal'
    return axis_name
        

def error_and_slope_plot(df, axis_name, window_size, num_windows, output_folder):
    x = df.index
    # Create a figure and a set of subplots
    fig, ax1 = plt.subplots(figsize=(70, 40))

    y2 = df['Vrms Trend rate']
    # Plot data on the secondary axis
    plt.plot(x, y2, color='b', label='Vrms Trend Rate',linewidth=4)
    # plt.xlabel('Date and Time')
    plt.ylabel('VelocityRMS (mm/sec)', color='k', fontsize=60)
    
    x_ticks_string = [i for i in df.index]
    x_ticks_indices = range(0, len(x), 3)
    x_ticks_labels = [x_ticks_string[j] for j in x_ticks_indices]
    
    # x_ticks_labels = ['Label{}'.format(i) for i in x_ticks]
    # labels_with_spaces = [f'{label}' for label in df.index]  # Add spaces to move labels to the left
    # plt.xticks(range(0, len(labels_with_spaces), 3))
    plt.xticks(x_ticks_indices, x_ticks_labels, rotation=15, ha='right', fontsize=60)
    plt.yticks(fontsize=60)

    # # Set the primary axis to dynamically choose tick locations and labels
    # ax1.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Add legends for both axes
    plt.legend(loc='upper right', fontsize = 60)
    plt.grid()
    title_name = df.index[0][:-6]+f'_{axis_name_for_report(axis_name)}'
    # plt.title(title_name+f'_{axis_name_for_report(axis_name)}', fontsize=50)
    trendline_output_file = os.path.join(output_folder, f'{title_name}_Error_&_Vrms Trend rate_{axis_name}.{config["output_format"]}')
    plt.savefig(trendline_output_file, format=config['output_format'])
    plt.close()
    
       
        
def normal_distribution_plot(original_df, dataframe_name, df_name, output_folder):
    df1 = original_df.sort_values(by='Value')

    # Calculate value ranges and their respective percentages
    value_ranges = [(0, 5), (5, 8), (8, np.inf)]
    value_range_details = []

    for start, end in value_ranges:
        filtered_data = df1[(df1['Value'] >= start) & (df1['Value'] < end)]
        data_percentage = len(filtered_data) / len(df1) * 100
        if start == 0 and end == 5:
            label = "Good (0-5 mm/s)"
        elif start == 5 and end == 8:
            label = "Warning (5-8 mm/s)"
        else:
            label = "Critical (>8 mm/s)"
        value_range_details.append(f'{label}: {data_percentage:.2f}%')

    # Define bin edges
    bin_edges = np.arange(0, df1['Value'].max() + 1, 1)

    # Calculate the histogram
    hist, _ = np.histogram(df1['Value'], bins=bin_edges, density=False)
    total_data = len(df1)
    percentage = hist / total_data * 100  # Calculate percentage of occurrences

    # Create the percentage plot with histogram
    plt.figure(figsize=(10, 6))

    # Define colors based on value ranges
    colors = ['lime', 'yellow', 'salmon']

    # Plot histogram bars with different colors
    legend_handles = []  # To store handles for custom legend
    for i, (start, end) in enumerate(value_ranges):
        color = colors[i]
        filtered_data = df1[(df1['Value'] >= start) & (df1['Value'] < end)]
        hist, _ = np.histogram(filtered_data['Value'], bins=bin_edges, density=False)
        hist_percentage = hist / total_data * 100
        handle = plt.bar(bin_edges[:-1], hist_percentage, width=1, align='edge', color=color, alpha=0.7)
        legend_handles.append(handle[0])  # Add the first handle to the custom legend

    # Overlay the normal distribution curve
    mu, std = df1['Value'].mean(), df1['Value'].std()
    x = np.linspace(min(df1['Value']), max(df1['Value']), 100)
    y = norm.pdf(x, mu, std) * 100  # Convert to percentage

    plt.plot(x, y, 'r-', label='Normal Distribution')
    plt.xlabel('Value Range')
    plt.locator_params(axis='x', nbins=21)
    plt.ylabel('Percentage')
    plt.title('Percentage Plot with Normal Distribution for {}_{}'.format(dataframe_name, df_name))

    # Display value range details inside the chart near the legend
    handles, labels = plt.gca().get_legend_handles_labels()

    # Create a combined list of handles and labels for the legend
    combined_handles = legend_handles + [handles[-1]] + handles[1:-1]  # Including red line and excluding first handle
    combined_labels = value_range_details + ['Normal Distribution'] + labels[
                                                                      1:-1]  # Including red line and excluding first label

    plt.legend(combined_handles, combined_labels, loc='upper right')
    ND_plot_name = f'Normal_Distribution_Plot_for_{dataframe_name}_{df_name}'  # Modify this line
    # output_file = os.path.join(output_folder, f'1.{ND_plot_name}.{config["output_format"]}')
    # plt.savefig(output_file, format=config['output_format'])

    # # Close the plot to release resources (optional)
    # plt.close()
    return y

def creating_directory(folder, list_of_sub_directories):
    for name in list_of_sub_directories:
        sub_diretories = folder + '\\' + name
        os.makedirs(sub_diretories, exist_ok=True)

def metrics_dataframe(metrics):
    metrics_value = []
    for ele in metrics:
        metrics_value.append(pd.DataFrame(ele).T)
    Metrics_Table = pd.concat(metrics_value)
    
    return Metrics_Table

def polynomial_and_trendplot(original_df, output_folder, dataframe, 
                             dataframe_name, df_name, config, directory_axis, 
                             data_duration_days):
    # Calculate the duration of data in number of days
    df = dataframe
    trending_methods = config['trending_methods']
    for method in trending_methods:
        plt.figure(figsize=(12, 6))
        if method['enabled'] and method['name'] == 'Trend Line':
            # data_duration_days = len(original_df)/48
            # Now, apply the trendline method to the original DataFrame
            trendline, slope = trend_line_method(original_df)
            # print('Trend Line Data')
            
        if method['enabled'] and method['name'] == 'Polynomial Trendline':
            degrees = method['degrees']
            colors = ['red', 'green']
            polynomial_trend_dfs = {}
            
            plt.figure(figsize=(12, 6))
            # Calculate polynomial trendlines for each degree
            for degree, color in zip(degrees, colors):
    
                x = np.arange(len(df))
                y = df['Value']
                # Fit a polynomial of the specified degree
                coefficients = np.polyfit(x, y, degree)
                polynomial = np.poly1d(coefficients)
                y=polynomial(x)
                polynomial_trend_dfs[degree] = y
                
               
            #     plt.plot(dataframe['DateTime'], y, color=color, label=f'Polynomial (Degree {degree})')
            # original_df['Trendline'] = trendline
            # plt.plot(original_df['DateTime'], original_df['Trendline'], 'b', label='Trendline')
            # plt.xlabel('Date and Time')
            # plt.ylabel('Value')
            # plt.title(f'{dataframe_name} Polynomial and Trendline (Degree_ {degree}) - {data_duration_days} days')
            # plt.legend()
            # # Save the trendline chart as an image in the specified output format
            # trendline_output_file = os.path.join(directory_axis, f'5.{dataframe_name}_Polynomial_Trendline_Degree_{degree}.{config["output_format"]}')
            # plt.savefig(trendline_output_file, format=config['output_format'])
            # # Close the plot to release resources (optional)
            # plt.close()

def plotting(dataframes, output_folder):  # to plots and get pics
    
    global corres_path
    
    # Initialize the list to store EMA Metrics
    ema_metrics = []
    # Initialize the list to store MA Metrics
    ma_metrics = []
    # Initialize the list to store Polynomial Trend Metrics
    poly_metrics = []
    # Initialize the list to store Trend Line Metrics
    TrendLine_metrics = []
    
    
    for file_name, item_path, axis_name, dataframe in dataframes:
        # print(f'Processing dataframe: {file_name}')
        
        relative_path = os.path.relpath(item_path, root_directory)
        output_file_path = os.path.join(output_folder, relative_path)
        corres_path = output_file_path + '\\' + file_name
        os.makedirs(corres_path, exist_ok=True)

        directory_axis = corres_path + '\\' + axis_name[-7:]
        os.makedirs(directory_axis, exist_ok=True)

        df = dataframe
        start_date = pd.to_datetime(df['DateTime'].min())
        end_date = pd.to_datetime(df['DateTime'].max())
        data_duration_days = ((end_date - start_date).days) + 1

        original_df = dataframe       
        
        # raw_data_plot(dataframe, directory_axis, file_name, axis_name, data_duration_days)
        
        # polynomial_and_trendplot(original_df, output_folder, dataframe, 
        #                               file_name, axis_name, config, directory_axis, 
        #                               data_duration_days)
        
        # Moving_Average = moving_average_plot(dataframe, file_name, axis_name, config, directory_axis,
        #                                       data_duration_days)
        # Polynomial_TrendLine = polynomial_trend(dataframe, file_name, axis_name, config, directory_axis,
        #                                         data_duration_days)
        # Exponential_Moving_Average = exp_moving_avg_plot(dataframe, directory_axis, file_name, axis_name, config,
        #                                                   data_duration_days)
        # normal_distribution_plot(original_df, file_name, axis_name, directory_axis)
        
        # TrendLine = TrendLine_Method(original_df, file_name, axis_name, directory_axis, config, data_duration_days)
        
        mtr = Trend_line_parreto_chart(original_df, file_name, axis_name, output_folder, config, data_duration_days, 7, 72)
        TrendLine_metrics_table = pd.concat(mtr, ignore_index=False)
        # TrendLine_metrics.append(TrendLine_metrics_table)
        # metrics_table = pd.concat(TrendLine_metrics, ignore_index=False)
        error_and_slope_plot(TrendLine_metrics_table, axis_name, 21, 4, output_folder)
        # print(metrics_table)
        # Moving_Average_Metrics = metrics_dataframe(Moving_Average)
        # ma_metrics.append(Moving_Average_Metrics)
        # ma_metrics_table = pd.concat(ma_metrics, ignore_index=False)
        # Polynomial_TrendLine_Metrics = metrics_dataframe(Polynomial_TrendLine)
        # poly_metrics.append(Polynomial_TrendLine_Metrics)
        # poly_metrics_table = pd.concat(poly_metrics, ignore_index=False) 
        # Exponential_Moving_Metrics = metrics_dataframe(Exponential_Moving_Average)
        # ema_metrics.append(Exponential_Moving_Metrics)
        # ema_metrics_table = pd.concat(ema_metrics, ignore_index=False)
        # TrendLine_Metrics = metrics_dataframe(TrendLine)
        # TrendLine_metrics.append(TrendLine_Metrics)
        # TrendLine_metrics_table = pd.concat(TrendLine_metrics, ignore_index=False)
        # # print(type(ma_metrics), len(ma_metrics), "----------------------------yooooo")
        # ma_metrics_table = TrendLine_metrics_table = poly_metrics_table = ema_metrics_table = pd.DataFrame()
        # if len(ma_metrics) > 0:
        #     ma_metrics_table = pd.concat(ma_metrics, ignore_index=False)  # pm
        # else:
        #     pass
        # if len(ema_metrics) > 0:
        #     ema_metrics_table = pd.concat(ema_metrics, ignore_index=False)  # pm
        # else:
        #     pass
        # if len(poly_metrics) > 0:
        #     poly_metrics_table = pd.concat(poly_metrics, ignore_index=False)  # pm
        # else:
        #     pass
        # if len(TrendLine_metrics) > 0:
        #     TrendLine_metrics_table = pd.concat(TrendLine_metrics, ignore_index=False)  # pm
        # else:
        #     pass
        
        # metrics_table = pd.concat([ma_metrics_table, ema_metrics_table,
        #                         poly_metrics_table, TrendLine_metrics_table])
        
        # metrics_table = pd.concat([TrendLine_metrics_table])
        # print(metrics_table)
        # table_name = str('Metrics_Table'+'_'+file_name)
        # # corres_path =
        # metrics_table.to_excel(corres_path + '\\' + f'{table_name}' + ".xlsx")
       
        # print("Plots generated successfully.")
    

# Main script  
if __name__ == '__main__':
    # Load configuration from JSON file
    config_file = 'D:/Code/config (1).json' 
    # config_file = 'C:/Users/Aureo/OneDrive - Aureole Technologies Private Limited/Vegam Projects/analytic_group/Trending/Trend_Generator_Config.json'
    with open(config_file, 'r') as f:
        config = json.load(f)

    list_of_sub_directories = ['Faults', 'Load', 'On_Off', 'RPM']

    current_time = datetime.datetime.now()
    time = current_time.strftime("%d_%m_%Y_%H_%M_%S")
    # Create a directory with timestamp
    directory = config['data_Output_folder'] + '\\' + 'Trending_plots' + '_' + time
    os.makedirs(directory, exist_ok=True)

    # Get the 'data_Input_folder' from the config
    directory_path = config['data_Input_folder']
    # Create an output folder if it doesn't exist
    output_folder = directory
    root_directory = directory_path

    for root, _, files in os.walk(root_directory):
        relative_path = os.path.relpath(root, root_directory)
        output_dir = os.path.join(output_folder)
        print(output_dir)
        # Create the corresponding directory structure in the output location
        os.makedirs(output_dir, exist_ok=True)

        # Call the preprocess_data function with the directory path
        dataframes = preprocess_data(root, output_dir)

        # Iterate through the dataframes and apply selected trending methods
        plotting(dataframes, output_folder)

    #pm works

    parent_folder= directory#'D:\vegam_projects\Trending'

    # Function to search for .jpeg files
    def find_jpeg_files(directory):
        # jpeg_files = []
        for root, _, files in os.walk(directory):
            jpeg_files = []
            for file in files:
                if file.lower().endswith('.jpeg'):
                    jpeg_files.append(os.path.join(root, file))
            if len(jpeg_files)>0:
                # print(jpeg_files,"this is pic name list")
                input_files= jpeg_files

                input_str = jpeg_files[0]  # 'D:\\vegam_projects\\Trending\\Trending_Plots\\Trending_plots_19_10_2023_19_27_38\\Faults\\Imbalance_Fault_data_SC_08\\X_Axis\\Faults_Combined_Moving_Average_X_Axis - 30 days.jpeg'
                index = input_str.find("_Axis")
                if index != -1:
                    output_str = input_str[:index] + "_Axis"
                else:
                    output_str = input_str  # If "_Axis" is not found, keep the original string

                print(output_str)

                output_file =output_str+ "_combined_plot.jpg"

                try:

                    # Desired dimensions for each image in the grid
                    width = 720  # Specify the desired width
                    height = 540  # Specify the desired height

                    # Load and resize all input images to the desired dimensions
                    images = [Image.open(file).resize((width, height)) for file in input_files]

                    # Calculate the total width and height for the combined image
                    total_width = width * 2
                    total_height = height * 3

                    # Create a new image with the calculated size
                    combined_image = Image.new('RGB', (total_width, total_height))


                    for i, img in enumerate(images):# Paste each image into the combined image at the correct position
                        x = (i % 2) * width
                        y = (i // 2) * height
                        combined_image.paste(img, (x, y))

                    combined_image.save(output_file)

                    print(f"Combined image saved as {output_file}")
                except Exception as e:
                    print(f"An error occurred while saving png: {str(e)}")

        # return jpeg_files

    # Search for .jpeg files in subdirectories
    jpeg_files = find_jpeg_files(parent_folder)

    import shutil

    # Source directory
    source_dir = output_folder #"D:\vegam_projects\Trending\Trending_Plots\Trending_plots_20_10_2023_10_20_55"
    print(source_dir)

    # List of subfolders
    subfolders = ['X_Axis', 'Y_Axis', 'Z_Axis']
    # # Record the end time
    # end_time = time.time()

    # # Calculate the elapsed time
    # elapsed_time = end_time - start_time

    # print(f"Script executed in {elapsed_time:.2f} seconds")
    