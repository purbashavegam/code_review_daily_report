import os
import json
import pandas as pd
import numpy as np
import plotly.express as px  # Updated import for Plotly
from scipy.stats import linregress
import plotly.graph_objects as go
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
matplotlib.use('TkAgg')  # Use the TkAgg backend (or another suitable one)
import shutil
from scipy.stats import norm
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import dataframe_image as dfi
import datetime

# Function to load, preprocess data and create plots 
def preprocess_data(directory_path, dataframes=None):
    if dataframes is None:
        dataframes = {}  # Initialize the dictionary if it doesn't exist

    folder_name = os.path.basename(directory_path)  # Extract the folder name

    print(f"Processing directory: {directory_path}")

    try:
        # Iterate through subdirectories (folder names) and files in the specified directory
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if os.path.isdir(item_path):
                # Recursively call preprocess_data for subdirectories
                preprocess_data(item_path, dataframes)
            elif item.endswith('.xlsx'):
                # Extract the file name without extension
                file_name = os.path.splitext(os.path.basename(item))[0]

                # # Calculate the relative path based on the current file being processed
                # relative_path = os.path.relpath(item_path, directory_path)

                df = pd.read_excel(item_path, sheet_name=None)  # Read all sheets into a dictionary
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
                    
                    dataframes[dataframe_name] = df_axis
                    # Print the generated dataframe names for debugging
                    print(f'Generated dataframe name: {dataframe_name}')

                    # Close the plot to release resources (optional)
                    plt.close()
    except Exception as e:
        print(f"Error processing directory '{directory_path}': {str(e)}")

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

def moving_average_trend(df, window_sizes):
    result_df = df.copy()

    for window_size in window_sizes:
        # Calculate the moving average
        result_df[f'MovingAverage_{window_size}'] = df['Value'].rolling(window=window_size).mean()
        result_df[f'MovingAverage_{window_size}'][:window_size] = df['Value'][:window_size]
    return result_df

# Moving average plots for corresponding windows
def moving_average_plot(dataframes, dataframe_name, config, directory_axis, data_duration_days):

    trending_methods = config['trending_methods']      

    ma_metrics = []
    for method in trending_methods:
    
        if method['enabled'] and method['name'] == 'Moving Average':
            window_sizes = method['window_sizes']
            
            moving_average_dfs = {}
            # Calculate moving averages for each window size
            for window_size in window_sizes:
                result_df = moving_average_trend(dataframe.copy(), [window_size])
                result_df.fillna(0)
                moving_average_dfs[window_size] = result_df
                # moving_average_dfs[window_size] = result_df  # Store the result_df in the moving_average_dfs dictionary
                
                column_name = list(result_df.columns)
                Moving_Average_evl_result = regression_metrics_dataframe(result_df['Value'], result_df[str(column_name[2])], 'Moving_Average_'+str(window_size)+'_'+df_name)
                ma_metrics.append(Moving_Average_evl_result)
                
                chart_name = f'{dataframe_name}_Moving_Average_{window_size} - {data_duration_days} days'
                y_column_name = f'MovingAverage_{window_size}'
                
                # Create a new figure and axis
                plt.figure(figsize=(12, 6))
    
                # # Plot the data using Seaborn
                # # sns.lineplot(data=result_df, x='DateTime', y=y_column_name, label=f'Moving Average (Window {window_size})')
                # # Plot the data using Seaborn
                # plt.plot(result_df['DateTime'], result_df[y_column_name], label=f'Moving Average (Window {window_size})')
                # plt.xlabel('Date and Time')
                # plt.ylabel('Moving Average')
                # plt.title(chart_name)
                # plt.legend()
    
                # # Save the individual chart as an image in the specified output format
                # output_file = os.path.join(directory_axis, f'{chart_name}.{config["output_format"]}')
                # plt.savefig(output_file, format=config['output_format'])
            
        combined_chart_name = f'{dataframe_name}_Combined_Moving_Average - {data_duration_days} days'
        # Plot all window trends on the same chart
        for i, (window_size, df_ma) in enumerate(moving_average_dfs.items()):
            y_column_name = f'MovingAverage_{window_size}'
            # sns.lineplot(data=df_ma, x='DateTime', y=y_column_name, label=f'Window {window_size}')
            plt.plot(df_ma['DateTime'], df_ma[str(y_column_name)], label=f'Window {window_size}')
        plt.xlabel('Date and Time')
        plt.ylabel('Moving Average Vrms')
        plt.title(combined_chart_name)
        plt.legend()

        # Save the combined chart as an image in the specified output format
        combined_output_file = os.path.join(directory_axis, f'{combined_chart_name}.{config["output_format"]}')
        plt.savefig(combined_output_file, format=config['output_format'])

        # Close the plot to release resources (optional)
        # plt.close()
    return ma_metrics

# Polynomial Trend plots
def polynomial_trend(dataframes, dataframe_name, config, directory_axis, data_duration_days):
    trending_methods = config['trending_methods']      

    # Calculate the duration of data in number of days
    df = dataframes
    start_date = pd.to_datetime(df['DateTime'].min())
    end_date = pd.to_datetime(df['DateTime'].max())
    data_duration_days = ((end_date - start_date).days) + 1
    poly_metrics = []
    for method in trending_methods:
        if method['enabled'] and method['name'] == 'Polynomial Trendline':
            degrees = method['degrees']
            
            polynomial_trend_dfs = {}
            # Calculate polynomial trendlines for each degree
            for degree in degrees:
    
                x = np.arange(len(df))
                y = df['Value']
                # Fit a polynomial of the specified degree
                coefficients = np.polyfit(x, y, degree)
                polynomial = np.poly1d(coefficients)
                y=polynomial(x)
                polynomial_trend_dfs[degree] = y
                print('Polynomial Data')
                print(y)
                # Create a new figure and axis for the trendline plot
                plt.figure(figsize=(12, 6))
            
                # Plot the original data
                # sns.lineplot(data=dataframe, x='DateTime', y='Value', label='Original Data', color='blue')
                plt.plot(dataframe['DateTime'], dataframe['Value'], 'b', label='Original Data')
            
                # Plot the polynomial trendline
                # sns.lineplot(x=dataframe['DateTime'], y=y, label=f'Polynomial Trendline (Degree {degree})', color='green')
                plt.plot(dataframe['DateTime'], y, 'g', label=f'Polynomial Trendline (Degree {degree})')
                
                plt.xlabel('Date and Time')
                plt.ylabel('Value')
                plt.title(f'{dataframe_name} Polynomial Trendline (Degree_ {degree}) - {data_duration_days} days')
                plt.legend()
                
                # Save the trendline chart as an image in the specified output format
                trendline_output_file = os.path.join(directory_axis, f'{dataframe_name}_Polynomial_Trendline_Degree_{degree}.{config["output_format"]}')
                plt.savefig(trendline_output_file, format=config['output_format'])
                # Close the plot to release resources (optional)
                # plt.close()

                Poly_evaluation_result = regression_metrics_dataframe(dataframe['Value'], pd.Series(y), 'ploy_degree_'+str(degree)+'_'+df_name)                             
                poly_metrics.append(Poly_evaluation_result)
    return poly_metrics

# Define a function for Exponential Moving Average (EMA)
def exponential_moving_average(data, alpha):
    ema = data.copy()
    ema['EMA'] = data['Value'].ewm(alpha=alpha, adjust=False).mean()
    return ema

def exp_moving_avg_plot(dataframe, directory_axis, config, data_duration_days):
    # Add code to save EMA plots similar to how you save other plots
    trending_methods = config['trending_methods']
    ema_metrics = []
    # Iterate through the saved exponential moving average (EMA) dataframes and generate plots
    for method in trending_methods:
        if method['name'] == 'Exponential Moving Average':
            ema_dfs = []
            if 'alpha' in method:  # Check if 'alpha' is defined in the method
                alpha = method['alpha']  # Get the alpha value from the config
                result_df = exponential_moving_average(dataframe.copy(), alpha)
                ema_dfs.append(result_df)
                EMA_evaluation_result = regression_metrics_dataframe(result_df['Value'], result_df['EMA'], 'EMA_'+df_name)
                ema_metrics.append(EMA_evaluation_result)
                
            for i, result_df in enumerate(ema_dfs):
                # days_in_duration = len(result_df)/48
                alpha = [method['alpha'] for method in trending_methods if method['name'] == 'Exponential Moving Average'][0]
                # Use the correct index for trending_methods
                chart_name = f'{dataframe_name}_EMA_alpha_{alpha} {data_duration_days} days'
                y_column_name = 'EMA'
        
                # Create a new figure and axis
                plt.figure(figsize=(12, 6))
        
                # Plot the data using Seaborn
                # sns.lineplot(data=result_df, x='DateTime', y=y_column_name, label=f'EMA (Alpha {alpha})')
                plt.plot(result_df['DateTime'], result_df[y_column_name], label=f'EMA (Alpha {alpha})')
                plt.xlabel('Date and Time')
                plt.ylabel('EMA')
                plt.title(chart_name)
                plt.legend()
        
                # Save the individual EMA chart as an image in the specified output format
                ema_output_file = os.path.join(directory_axis, f'{chart_name}.{config["output_format"]}')
                plt.savefig(ema_output_file, format=config['output_format'])
        
                # Close the plot to release resources (optional)
                # plt.close()
    # return ema_metrics
    return ema_metrics


def normal_distribution_plot(original_df, output_folder):
    
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
     plt.title('Percentage Plot with Normal Distribution for {}'.format(dataframe_name))
 
     # Display value range details inside the chart near the legend
     handles, labels = plt.gca().get_legend_handles_labels()
 
     # Create a combined list of handles and labels for the legend
     combined_handles = legend_handles + [handles[-1]] + handles[1:-1]  # Including red line and excluding first handle
     combined_labels = value_range_details + ['Normal Distribution'] + labels[1:-1]  # Including red line and excluding first label
     
     plt.legend(combined_handles, combined_labels, loc='upper right')
     ND_plot_name = f'Normal_Distribution_Plot_for_{dataframe_name}'  # Modify this line
     output_file = os.path.join(output_folder, f'{ND_plot_name}.{config["output_format"]}')
     plt.savefig(output_file, format=config['output_format'])
 
     # Close the plot to release resources (optional)
     # plt.close()
     return y

def trend_line_method(df):
    x = df['DateTime'].astype(np.int64) // 10**9  # Convert to Unix timestamp (seconds)
    slope, intercept, _, _, _ = linregress(x, df['Value'])
    trendline = intercept + slope * x
    # print()
    return trendline, slope

def TrendLine_Method(original_df, output_folder, config, data_duration_days):
    trending_methods = config['trending_methods']
    trl_metrics = []
    # Iterate through the saved exponential moving average (EMA) dataframes and generate plots
    for method in trending_methods:
        if method['enabled'] and method['name'] == 'Trend Line':
            # data_duration_days = len(original_df)/48
            # Now, apply the trendline method to the original DataFrame
            trendline, slope = trend_line_method(original_df)
            print('Trend Line Data')
            
            original_df['Trendline'] = trendline

            TRL_evaluation_result = regression_metrics_dataframe(original_df['Value'], trendline, 'Trend_Line_'+df_name)
            trl_metrics.append(TRL_evaluation_result)
            # Create a new figure and axis for the original data plot
            plt.figure(figsize=(12, 6))
        
            # Plot the original data using Seaborn, replace 'YourColumnName' with the actual column name
            # sns.lineplot(data=original_df, x='DateTime', y='Value', label='Original Data', color='blue')
            plt.plot(original_df['DateTime'], original_df['Value'], 'b', label='Original Data')
            # Plot the trendline on the same chart as the original data
            # sns.lineplot(data=original_df, x='DateTime', y='Trendline', label='Trendline', color='red')
            plt.plot(original_df['DateTime'], original_df['Trendline'], 'r', label='Trendline')
            plt.xlabel('Date and Time')
            plt.ylabel('Value')
            plt.title(f'{dataframe_name} Trendline - {data_duration_days} days')
            plt.legend()
            
            # Save the combined chart as an image in the specified output format
            trendline_output_file = os.path.join(output_folder, f'{dataframe_name}_Trendline.{config["output_format"]}')
            plt.savefig(trendline_output_file, format=config['output_format'])
        
            # Close the plot to release resources (optional)
            # plt.close()
        
            print(f'Individual and combined plots, along with trendline, generated for {dataframe_name}')

    return trl_metrics

def creating_directory(folder, list_of_sub_directories):
    for name in list_of_sub_directories:
        sub_diretories = folder + '\\'+name
        os.makedirs(sub_diretories, exist_ok=True)

def metrics_dataframe(metrics):
    metrics_value = []
    for ele in metrics:
        metrics_value.append(pd.DataFrame(ele).T)
    Metrics_Table = pd.concat(metrics_value)
    return Metrics_Table

def combine_plots_into_image(dataframes, dataframe, original_df, 
                              directory_axis, dataframe_name, config):
    plt.figure(figsize=(22, 20))

    # Generate and plot each type of plot
    plt.subplot(3, 2, 1)
    normal_distribution_plot(original_df, directory_axis)

    plt.subplot(3, 2, 2)
    exp_moving_avg_plot(dataframe, directory_axis, config, data_duration_days)

    plt.subplot(3, 2, 3)
    TrendLine_Method(original_df, directory_axis, config, data_duration_days)
    
    plt.subplot(3, 2, 4)
    polynomial_trend(dataframes, dataframe_name, config, directory_axis, data_duration_days)
    
    plt.subplot(3, 2, 5)
    moving_average_plot(dataframes, dataframe_name, config, directory_axis, data_duration_days)
    # plt.subplot(3, 2, 6)
    # generate_moving_average_plots(ma)

    plt.tight_layout()

    # Save the combined figure as a PNG image
    plt.savefig(directory_axis+'\\combined_plots.png', format='png', bbox_inches='tight', pad_inches=0.8)


# Main script  
if __name__ == '__main__':
    # Load configuration from JSON file
    config_file = 'C:/Users/Aureo/OneDrive - Aureole Technologies Private Limited/Vegam Projects/analytic_group/Trending/Trend_Generator_Config.json'  
    with open(config_file, 'r') as f:
        config = json.load(f)

    list_of_sub_directories = ['Faults', 'Load', 'On_Off', 'RPM']
    
    current_time = datetime.datetime.now()
    time = current_time.strftime("%d_%m_%Y_%H_%M_%S")
    #Create a directory with timestamp
    directory = config['data_Output_folder']+'\\'+'Trending_plots'+'_'+time
    os.makedirs(directory, exist_ok=True)
    creating_directory(directory, list_of_sub_directories)
        
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
        dataframes = preprocess_data(root)
                
        # print(folder_name)
        #Initialize the list to store EMA Metrics
        ema_metrics = []
        #Initialize the list to store MA Metrics
        ma_metrics = []
        #Initialize the list to store Polynomial Trend Metrics
        poly_metrics = []
        #Initialize the list to store Trend Line Metrics
        TrendLine_metrics = []
        # Iterate through the dataframes and apply selected trending methods
        for dataframe_name, dataframe in dataframes.items():
            print(f'Processing dataframe: {dataframe_name}')
            len(dataframe_name)
           
            folder_dir = output_dir+'\\'+dataframe_name[:-7]
            os.makedirs(folder_dir, exist_ok=True)
            df_name = dataframe_name[-6:]
            directory_axis = folder_dir+'\\'+df_name
            os.makedirs(directory_axis, exist_ok=True)
            
            df = dataframes[dataframe_name]
            start_date = pd.to_datetime(df['DateTime'].min())
            end_date = pd.to_datetime(df['DateTime'].max())
            data_duration_days = ((end_date - start_date).days) + 1
            
            original_df = dataframes[dataframe_name]
            
            Moving_Average = moving_average_plot(dataframe, dataframe_name, config, directory_axis, data_duration_days)
            Polynomial_TrendLine = polynomial_trend(dataframe, dataframe_name, config, directory_axis, data_duration_days)
            Exponential_Moving_Average = exp_moving_avg_plot(dataframe, directory_axis, config, data_duration_days)
            Normal_Distribution = normal_distribution_plot(original_df, directory_axis)
            TrendLine = TrendLine_Method(original_df, directory_axis, config, data_duration_days)
    
            
            # combine_plots_into_image(original_df, dataframe, original_df, 
            #                               directory_axis, dataframe_name, config)
        
            Moving_Average_Metrics = metrics_dataframe(Moving_Average)
            ma_metrics.append(Moving_Average_Metrics)
            Polynomial_TrendLine_Metrics = metrics_dataframe(Polynomial_TrendLine)
            poly_metrics.append(Polynomial_TrendLine_Metrics)
            Exponential_Moving_Metrics = metrics_dataframe(Exponential_Moving_Average)
            ema_metrics.append(Exponential_Moving_Metrics)
            TrendLine_Metrics = metrics_dataframe(TrendLine)
            TrendLine_metrics.append(TrendLine_Metrics)
            
        ma_metrics_table = pd.concat(ma_metrics, ignore_index=None)
        ema_metrics_table = pd.concat(ema_metrics, ignore_index=None)
        poly_metrics_table = pd.concat(poly_metrics, ignore_index=None)
        TrendLine_metrics_table = pd.concat(TrendLine_metrics, ignore_index=None)
            
        metrics_table = pd.concat([ma_metrics_table, ema_metrics_table,
                                    poly_metrics_table, TrendLine_metrics_table])
        table_name = 'Metrics_Table'
        metrics_table.to_excel(folder_dir+'\\'+f'{dataframe_name}_{table_name}'+".xlsx")
        plt.savefig(folder_dir + '\\' + f'{dataframe_name}_{table_name}'+'.jpeg')
        table_path = folder_dir+ '\\' + f'{dataframe_name}_{table_name}' +'.jpeg'
        df_styled = metrics_table.style.background_gradient() 
        dfi.export(df_styled,table_path)
        
        print("Plots generated successfully.")

        
        
            
            
            
            
            
            
                
                
        
        