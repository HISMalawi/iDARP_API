from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
import logging
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

class RecordExpiredException(Exception):
    pass

class UsernameAndOTPModelBackend(BaseBackend):
    def authenticate(self, request, username=None, otp=None, **kwargs):
        User = get_user_model()
        
        # Check if username is an org_email or phone number
        if username is not None:
            if '@' in username:
                # Authenticate using org_email
                try:
                    user = User.objects.get(org_email=username, otp=otp)

                    if user.otp_last_updated is not None:
                        record_timestamp = user.otp_last_updated

                        # Get the current time
                        current_time = timezone.now()

                        # Calculate the time difference between the current time and the record timestamp
                        time_difference = current_time - record_timestamp

                        # Check if the time difference is within the desired range (2 minutes)
                        if time_difference <= timedelta(minutes=2):
                            return user
                        else:

                            raise RecordExpiredException("OTP Expired")             
                    
                except User.DoesNotExist:
                    pass

            else:
                # Authenticate using phone number
                try:
                    user = User.objects.get(phone=username, otp=otp)

                    if user.otp_last_updated is not None:
                        record_timestamp = user.otp_last_updated

                        # Get the current time
                        current_time = timezone.now()

                        # Calculate the time difference between the current time and the record timestamp
                        time_difference = current_time - record_timestamp

                        # Check if the time difference is within the desired range (2 minutes)
                        if time_difference <= timedelta(minutes=2):
                            return user
                        else:

                            raise RecordExpiredException("OTP Expired")
                            
                    
                except User.DoesNotExist:
                    pass

        return None
