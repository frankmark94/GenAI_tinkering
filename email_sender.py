import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class EmailSender:
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587):
        """
        Initialize EmailSender with SMTP settings
        
        Args:
            smtp_server (str): SMTP server address
            smtp_port (int): SMTP server port
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        
    def send_results(self, json_data, sender_email, sender_password, recipient_email):
        """
        Send email with JSON results
        
        Args:
            json_data (dict): JSON data to send
            sender_email (str): Email address to send from
            sender_password (str): App password for sender's email
            recipient_email (str): Email address to send to
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"API Response Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Format JSON data for email body
            formatted_json = json.dumps(json_data, indent=2)
            email_body = f"""
            Here are the results from your API query:
            
            {formatted_json}
            
            This is an automated message.
            """
            
            msg.attach(MIMEText(email_body, 'plain'))
            
            # Create SMTP session
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
                
            print(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False 