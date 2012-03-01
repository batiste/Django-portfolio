from django.conf import settings
from django.contrib.auth.models import User, check_password
import uuid


def create_user():
    return User.objects.create(username='anon:'+str(uuid.uuid4()))


class MarketBackend(object):
    """
    Authenticate anonymous users
    """
    supports_inactive_user = True

    def authenticate(self, user=None):
        if user:
            return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None