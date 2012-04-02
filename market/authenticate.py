from django.conf import settings
from django.contrib.auth.models import User, check_password
import uuid
from django.contrib.auth.backends import ModelBackend

def create_user():
    return User.objects.create(username='anon:'+str(uuid.uuid4()))


class AnonymousBackend(object):
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


class EmailBackend(ModelBackend):
    def authenticate(self, email=None, password=None):
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except (User.DoesNotExist,  User.MultipleObjectsReturned):
            pass
        return None