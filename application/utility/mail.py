import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from pathlib import Path
from dotenv import dotenv_values
from typing import Union


def retrieve_env_values():
    _parent_dir = Path(__file__).parent.parent.parent
    _dotenv_dir = _parent_dir / '.env'
    return dotenv_values(_dotenv_dir)


class Email:
    env_values = retrieve_env_values()

    sender_email: str = env_values.get('EMAIL_ADDRESS')
    receiver_email: str = env_values.get('EMAIL_RECEIVER')
    subject: str = "tempehomat"
    message: str = 'test'
    password: str = env_values.get('EMAIL_PASSWORD')

    def _create_mime(self) -> MIMEMultipart:
        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = self.receiver_email
        msg["Subject"] = self.subject

        msg.attach(MIMEText(self.message, "plain"))
        return msg

    def send(self, message: str, email: Union[None, str] = None):
        if email:
            self.receiver_email = email
            # pass

        self.message = message
        msg = self._create_mime()
        server = None
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.sender_email, self.password)
            server.sendmail(self.sender_email, self.receiver_email, msg.as_string())
            logging.info("Email sent successfully!")
        except Exception as e:
            logging.info(f"An error occurred: {e}")
        finally:
            if server:
                server.quit()


def send_mail(message: str):
    Email().send(message)
