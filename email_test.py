
# Here's a Python test script that checks if the Gmail credentials provided in a .env file can send an email successfully. 
# This script uses the `dotenv` library to load environment variables and `smtplib` for sending emails.

# First, ensure you have `python-dotenv` installed:
# pip install python-dotenv

# The .env file should contain:
# GMAIL_ADDRESS=your_gmail_address
# GMAIL_PASSWORD=your_gmail_password

# The script will attempt to send a test email to the same Gmail address. 

# Save this script as `test_email.py` and run it with Python.

import os
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText

# Load environment variables from .env file
load_dotenv()

# Email details
sender_email = os.getenv("EMAIL_HOST_USER")
receiver_email = sender_email  # Sending the email to the same address for testing
password = os.getenv("EMAIL_HOST_PASSWORD")
subject = "Test Email from Python Script"
body = "This is a test email sent from Python script to verify Gmail SMTP configuration."
print("sender_email:", sender_email)
print ("receiver_email:", receiver_email)
print("password:", password)

# Create MIMEText object
msg = MIMEText(body)
msg["Subject"] = subject
msg["From"] = sender_email
msg["To"] = receiver_email

# Send the email
try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
    print("Email sent successfully.")
except Exception as e:
    print(f"Error: {e}")

# Note: For this script to work, 'Less secure app access' must be enabled in your Google account, 
# or you should use an App Password if 2-Step Verification is enabled.

