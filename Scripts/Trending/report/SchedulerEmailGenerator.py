# SchedulerEmailGenerator.py
import json
import os
from datetime import datetime, timedelta
import time
import logging
# from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import fitz
import pytz
import schedule
from Scripts.Trending.report.ReportGeneratorFacade import ReportGeneratorFacade
from Scripts.Trending.report.logger_file import logger

# log_folder_path = 'C:\\Vegam\\Trends_alert\\logs'
# # log_folder_path = 'logs'
# if not os.path.exists(log_folder_path):
#     try:
#         os.makedirs(log_folder_path)
#         logging.info(f'Created "{log_folder_path}" folder.')
#     except Exception as e:
#         logging.info(f'Error creating "{log_folder_path}" folder: {str(e)}')
#
# logger = logging.getLogger()
# log_format = '%(asctime)s - [%(filename)s::%(lineno)d] - %(levelname)12s - %(threadName)22s  - %(funcName)s -' \
#              ' %(message)s'
# logging.basicConfig(
#     format=log_format,
#     datefmt='%Y-%m-%d %H:%M:%S',
#     level=logging.DEBUG
# )
#
# # file_handler = RotatingFileHandler(
# #     'C:\\Vegam\\Trends_alert\\logs\\daily_report.log', maxBytes=200 * 1024 * 1024, backupCount=10, mode='a'
# # )
#
# file_handler = TimedRotatingFileHandler(f'C:\\Vegam\\Trends_alert\\logs\\daily_report.log', when='h', interval=24, backupCount=365)
#
# # file_handler = RotatingFileHandler(
# #     'logs/daily_report.log', maxBytes=200 * 1024 * 1024, backupCount=10, mode='a'
# # )
# file_handler.setFormatter(logging.Formatter(log_format))
# logger.addHandler(file_handler)


# trends_json = "C:\\Trends_services\\Trends.json"
trends_json = "C:\\Vegam\\Trends_alert\\Daily_Report_Trends.json"

try:
    '''Check if the file exists'''
    if not os.path.isfile(trends_json):
        logger.info(f"File '{trends_json}' does not exist.")
        raise FileNotFoundError(f"File '{trends_json}' does not exist.")

    '''Check if the file is empty'''
    if os.path.getsize(trends_json) == 0:
        logger.info(f"File '{trends_json}' is empty.")
        raise ValueError(f"File '{trends_json}' is empty.")

    with open(trends_json, 'r') as json_file:
        json_data = json.load(json_file)

except FileNotFoundError as e:
    logger.error(str(e))
except ValueError as e:
    logger.error(str(e))
except Exception as e:
    logger.error(f"An unexpected error occurred: {str(e)}")




class SchedulerEmailGenerator:
    def __init__(self):
        try:
            scheduler_facade_timing = json_data["scheduler_data"]["scheduler_facade_timing"]
            scheduler_email_timing = json_data["scheduler_data"]["scheduler_email_timing"]

            logger.info("The scheduler started waiting for the report generator scheduled times...")
            schedule.every().day.at(scheduler_facade_timing).do(self.scheduler_for_facade_running)
            # schedule.every(10).seconds.do(self.scheduler_for_facade_running)
            logger.info("The scheduler started waiting for the email scheduled times...")
            schedule.every().day.at(scheduler_email_timing).do(self.email_report_to_send_excel)
            # schedule.every(40).minutes.do(self.email_report_to_send_excel)

        except Exception as w:
            logging.error(f"An error occurred during initialization in ReportGeneratorFacade: {str(w)}")

    def scheduler_for_facade_running(self):
        try:
            print("entered in facade class")
            logger.info("Scheduled time of the ReportGeneratorFacade class encountered, entered to the function.")
            try:
                def get_current_ist_date():
                    try:
                        ist_timezone = pytz.timezone('Asia/Kolkata')
                        utc_now = datetime.utcnow()
                        ist_now = utc_now.replace(tzinfo=pytz.utc).astimezone(ist_timezone)
                        formatted_ist_date = ist_now.strftime("%d_%m_%Y")
                        print(type(formatted_ist_date))

                        return formatted_ist_date
                    except Exception as d:
                        print(d)

                # Example usage
                # print(get_current_ist_date())

                starting_date = get_current_ist_date()

                # '''Check if the file exists'''
                # if not os.path.isfile(trends_json):
                #     raise FileNotFoundError(f"File '{trends_json}' does not exist.")
                #
                # '''Check if the file is empty'''
                # if os.path.getsize(trends_json) == 0:
                #     raise ValueError(f"File '{trends_json}' is empty.")
                #
                # with open(trends_json, 'r') as json_file:
                trends_Config_json = json_data
                area_check_lists = trends_Config_json["trends"]["area_check"]
                print(area_check_lists)
                # ReportFacadeObj = ReportGeneratorFacade(trends_json, area_check_lists)
                # ReportFacadeObj.make_report()
                for area in area_check_lists:
                    logger.info(f"Report work is started for :{area}")
                    ReportFacadeObj = ReportGeneratorFacade(trends_json, area, starting_date)
                    ReportFacadeObj.make_report()
                    time.sleep(15)


            except FileNotFoundError as e:
                logger.error(str(e))
            except ValueError as e:
                logger.error(str(e))
            except Exception as e:
                logger.error(f"An unexpected error occurred: {str(e)}")
        except Exception as e:
            logger.error(f"Error in starting the scheduler for ReportGeneratorFacade: {e}")

    # import fitz  # PyMuPDF

    def is_pdf_blank(self,pdf_path):
        try:
            doc = fitz.open(pdf_path)

            text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()

            if not text.strip():
                return True
            else:
                return False

        except Exception as e:
            logger.info(f"Error while reading PDF during check: {e}")
            return False
    def file_availability_check(self, folder_path, file_list):
        try:
            existing_files = []
            for file_name in file_list:
                location_wise_sub_folder_name = file_name.split(".")[0]
                folder_path_area = f"{folder_path}{location_wise_sub_folder_name}\\{file_name}"
                if os.path.exists(f"{folder_path}{location_wise_sub_folder_name}") and os.path.isfile(folder_path_area) and self.is_pdf_blank(folder_path_area)==False:
                    existing_files.append(file_name)
            if len(existing_files):
                logger.info("Files present in the directory:")
                return existing_files
            else:
                logger.info("file not present!!!!!!!!!!!!!!")
                existing_files = []
                return existing_files
        except Exception as ex:
            logger.error("Error in file availability check - ",ex)

    def folder_availability_check(self, folder_path, file_list):
        try:
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                logger.info(f"The folder '{folder_path}' exists.")
                file_avlbl_list = self.file_availability_check(folder_path, file_list)
                return file_avlbl_list
            else:
                logger.info(f"The folder '{folder_path}' does not exist!!!!!!!!!!!!!!")
                file_avlbl_status = []
                return file_avlbl_status
        except Exception as ex:
            logger.error("Error in folder_availability_check - ", ex)


    def email_report_to_send_excel(self):
        logger.info("Scheduled time of the email_report_to_send_excel function encountered, entered to the function.")
        try:
            curr_date=datetime.now()
            folder_name = curr_date.strftime("%d_%m_%Y")
            folder_path= f"{json_data['scheduler_data']['upload_pdf_path']}\\{folder_name}\\"
            file_list = json_data["scheduler_data"]["upload_file_list"]

            folder_status_list = self.folder_availability_check(folder_path, file_list)

            if len(folder_status_list)==3:
                logger.info("started mail service for")
                sender_email = json_data["scheduler_data"]["sender_email_vegam"]  # personaltest
                sender_password = json_data["scheduler_data"]["sender_password_vegam"]  # 'jnjatyvjqkfrlaqu'

                recipient_email = json_data["scheduler_data"]["mail_id_list"]
                cc_recipients = json_data["scheduler_data"]["cc_recipients_list"]

                end_date = curr_date.replace(hour=8, minute=0, second=0, microsecond=0)
                end_date_str = end_date.strftime('%d-%m-%Y %H:%M:%S')
                start_date = end_date-timedelta(days=1)
                start_date_str = start_date.strftime('%d-%m-%Y %H:%M:%S')
                subject = json_data["scheduler_data"]["email_subject"]
                message_body = f"<b>DAILY REPORT : {start_date_str} to {end_date_str}</b><br><br>" + \
                               "Dear Team, <br><br>" + \
                               f"{json_data['scheduler_data']['mail_context']}<br>" + \
                               "<br>Regards, <br>Vegam Team<br>"


                message = MIMEMultipart()
                message['From'] = sender_email
                message['To'] = ', '.join(recipient_email)
                message['Cc'] = ', '.join(cc_recipients)
                message['Subject'] = subject

                message.attach(MIMEText(message_body, 'html'))

                # Attach the Excel file
                for file_path in folder_status_list:
                    location_wise_sub_folder_name = file_path.split(".")[0]
                    actual_file_path = f"{json_data['scheduler_data']['upload_pdf_path']}\\{folder_name}\\{location_wise_sub_folder_name}\\{file_path}"
                    attachment = open(actual_file_path, 'rb')
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename= {file_path}')
                    message.attach(part)

                try:
                    smtp_server = json_data["scheduler_data"]["smtp_server_outlook"]
                    smtp_port = 587

                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, recipient_email, message.as_string())
                    server.sendmail(sender_email, cc_recipients, message.as_string())
                    server.quit()

                    logger.info("Email sent successfully!")
                except Exception as e:
                    logger.error(f"Error in mail sending procedure : {str(e)}")

        except Exception as ex:
            logger.error("Exception in mail sending script on configuration side as", ex)
    def run_schedule(self):
        try:
            while True:
                schedule.run_pending()
                # time.sleep(1)
        except Exception as ex:
            logger.error("scheduler running problem occurred - ",ex)


if __name__ == "__main__":
    try:
        my_instance = SchedulerEmailGenerator()
        my_instance.run_schedule()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")


# command for exe[python 3.9]

# pyinstaller --onefile --additional-hooks-dir="D:\vegam_work_drive\BAL
# CO_PROJECT\analytics_daily_report_supriya\Vegam_Analytics\custom_hooks" --add-data "D:\vegam_work_drive\BALCO_PROJECT\analytics_daily_report_supriya\Vegam_Analytics\Scripts\Trendin
# g\report\DailyReportGenerator.py;Scripts\Trending\report" --add-data "D:\vegam_work_drive\BALCO_PROJECT\analytics_daily_report_supriya\Vegam_Analytics\Scripts\Trending\report\Extra
# ctMetaData.py;Scripts\Trending\report" --add-data "D:\vegam_work_drive\BALCO_PROJECT\analytics_daily_report_supriya\Vegam_Analytics\Scripts\Trending\report\ExtractSensorData.py;Scr
# ipts\Trending\report" --add-data "D:\vegam_work_drive\BALCO_PROJECT\analytics_daily_report_supriya\Vegam_Analytics\Scripts\Trending\report\AverageCalculator.py;Scripts\Trending\rep
# ort" --add-data "D:\vegam_work_drive\BALCO_PROJECT\analytics_daily_report_supriya\Vegam_Analytics\Scripts\Trending\report\ReportGeneratorFacade.py;Scripts\Trending\report" --hidden
# -import=fitz --hidden-import=pyarrow --hidden-import=psutil --hidden-import=requests --hidden-import=docx --hidden-import=pandas --hidden-import=docx2pdf --hidden-import=matplotlib
#  --hidden-import=xlsxwriter --hidden-import=openpyxl --hidden-import=scipy --clean --name "DailyReportGeneratorAndMail" "D:\vegam_work_drive\BALCO_PROJECT\analytics_daily_report_supriya\Vegam_Analytics\Scripts\Trending\report\SchedulerEmailGenerator.py"
