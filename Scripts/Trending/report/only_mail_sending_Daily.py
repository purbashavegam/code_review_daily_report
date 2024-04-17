'''
OBJECTIVE : #COMMON
This file is required in case for sending the mail only.

'''



import json
import logging
import os
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

trends_json = "C:\\Vegam\\Trends_alert\\Daily_Report_Trends.json"

try:
    '''Check if the file exists'''
    if not os.path.isfile(trends_json):
        logging.info(f"File '{trends_json}' does not exist.")
        raise FileNotFoundError(f"File '{trends_json}' does not exist.")

    '''Check if the file is empty'''
    if os.path.getsize(trends_json) == 0:
        logging.info(f"File '{trends_json}' is empty.")
        raise ValueError(f"File '{trends_json}' is empty.")

    with open(trends_json, 'r') as json_file:
        json_data = json.load(json_file)

except FileNotFoundError as e:
    logging.error(str(e))
except ValueError as e:
    logging.error(str(e))
except Exception as e:
    logging.error(f"An unexpected error occurred: {str(e)}")


curr_date=datetime.now()
logging.info("started mail service for")
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

folder_status_list=["C://Vegam//Trends_alert//report//22_03_2024//CHP.pdf","C://Vegam//Trends_alert//report//22_03_2024//Cooling Tower Area.pdf","C://Vegam//Trends_alert//report//22_03_2024//Compressor House.pdf"]

# Attach the Excel file
for file_path in folder_status_list:
    location_wise_sub_folder_name = file_path.split(".")[0]
    actual_file_path = file_path
    attachment = open(actual_file_path, 'rb')
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    filename = os.path.basename(file_path)
    part.add_header('Content-Disposition', f'attachment; filename= {filename}')
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

    logging.info("Email sent successfully!")
except Exception as e:
    logging.error(f"Error in mail sending procedure : {str(e)}")

