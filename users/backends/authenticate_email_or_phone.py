from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

class EmailOrPhoneModelBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        
        # Check if username is an org_email or phone number
        if username is not None:
            if '@' in username:
                # Authenticate using org_email
                try:
                    user = User.objects.get(org_email=username)
                    
                    if user.check_password(password):
                        return user
                except User.DoesNotExist:
                    pass
            else:
                # Authenticate using phone number
                try:
                    user = User.objects.get(phone=username)
                    if user.check_password(password):
                        return user
                except User.DoesNotExist:
                    pass

        return None
