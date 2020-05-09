## Aggregating Looker PDF reports for external clients via Looker API
import time
import os
import shutil
import email, smtplib, ssl
import looker_sdk

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import cast, Dict, Optional
from looker_sdk import models

#API credentials here to access Looker
sdk = looker_sdk.init31(".../looker.ini")

#Create a folder where you can store the pdfs.
os.mkdir(".../campaign_performance")
directory = ".../campaign_performance/"

#Generate a dataframe of user_ids, names, emails, and list of campaign ids

user_id = [
    #Parsed list in production
]

#Function to generate a list of campaign reports per user
def file_gen():
    for user in user_id:
        #Creates a directory with the user_id so that we can identify who gets which reports.
        os.mkdir(directory + user)

        #Placeholder list for a dynamically generated list of campaigns per user.
        campaign_id = [
            #Parsed list in production
        ]
        for cid in campaign_id:
            def get_pdf():
                filters = 'url_filter_settings_from_Looker_link'
                dashboard_number=326
                task = sdk.create_dashboard_render_task(
                    dashboard_id=dashboard_number,
                    result_format="pdf",
                    body=models.CreateDashboardRenderTask(
                        dashboard_style="tiled",
                        dashboard_filters=filters
                    ),
                    width=545,
                    height=842
                )

                if not (task and task.id):
                    print("Render failed")

                #Poll the render task until it completes - needs to sleep or else render fails.
                elapsed = 0.0
                delay = 0.5  # wait .5 seconds
                while True:
                    poll = sdk.render_task(task.id)
                    if poll.status == "failure":
                        print(poll)
                        print("Render failed")
                    elif poll.status == "success":
                        break

                    time.sleep(delay)
                    elapsed += delay
                print(f"Render task completed in {elapsed} seconds")

                result = sdk.render_task_results(task.id)
                filename = directory + user + "/" + cid + "_file.pdf"
                with open(filename, "wb") as f:
                    f.write(result)
                print(f'Dashboard pdf saved as "{filename}"')

            get_pdf()
file_gen()
print("PDFs generated.")

#Function to group attachments into one email per user.
filename = []
for user in user_id:
    for root, dirs, files in os.walk(directory + user):
        for file in files:
            if file.endswith('.pdf'):
                filename.append(file)

for user in user_id:
    def email_gen():

        #Change these values accordingly. One thing to note is that if you are using Gmail, you will need to
        #edit the security settings to allow an external application to send out emails.
        subject = "Pollen Campaign Performance Report"
        body = "Hi there, here is your campaign performance report."
        sender_email = "SENDER_EMAIL@pollen.co"
        receiver_email = "RECEIVER_EMAIL@pollen.co"
        password = "PASSWORD" #alternatively use this -> input("Type your password and press enter:")

        # Create a multipart message and set headers
        message = MIMEMultipart()
        message["From"] = "SENDER_EMAIL@pollen.co"
        message["To"] = "RECEIVER_EMAIL@pollen.co"
        message["Subject"] = "Report for " + user

        # Add body to email
        message.attach(MIMEText(body, "plain"))
        
        for f in filename:
            g = directory + user + "/" + f
            # Open PDF file in binary mode
            with open(g, "rb") as attachment:
                # Add file as application/octet-stream
                # Email client can usually download this automatically as attachment
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            # Encode file in ASCII characters to send by email    
            encoders.encode_base64(part)

            # Add header as key/value pair to attachment part
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {g}",
            )

            # Add attachment to message and convert message to string
            message.attach(part)
            text = message.as_string()

        # Log in to server using secure context and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, text)

    email_gen()
print("Emails generated.")

#Removes the directory after everything is done.
shutil.rmtree(directory)
print("Directory removed.")

print("Done!")
