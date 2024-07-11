from abc import ABC, abstractmethod
from django.conf import settings
from twilio.rest import Client
import vonage
import logging

logger = logging.getLogger(__name__)

class OTPSender(ABC):
    @abstractmethod
    def send_otp(self, phone_number: str, otp_code: str) -> bool:
        pass

class VonageSender(OTPSender):
    
    client = vonage.Client(key=settings.VONAGE_KEY, secret=settings.VONAGE_SECRET)
    sms = vonage.Sms(client)

    def send_otp(self, phone_number: str, otp_code: str):

        responseData = self.sms.send_message(
            {
                "from": "Vonage APIs",
                "to": phone_number,
                "text": otp_code,
            }
        )

        if responseData["messages"][0]["status"] == "0":
            return True
        else:
            return False

class TwilioSender(OTPSender):
    
    account_sid = settings.TWILIO_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    twilio_phone_number = settings.TWILIO_PHONE_NUMBER

    client = Client(account_sid, auth_token)

    def send_otp(self, phone_number: str, otp_code: str):

        # Send a message
        message = self.client.messages.create(
            body=otp_code,
            from_=self.twilio_phone_number,
            to=phone_number
        )

        # Check the status of the message

        if message.sid:
            return True
        else:
            return False
