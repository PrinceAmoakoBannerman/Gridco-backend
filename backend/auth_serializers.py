from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Allow clients to submit either username or email in the 'username' field.

    If an email is provided and matches a user, replace the username field
    with that user's username before delegating to the parent serializer.
    """

    def validate(self, attrs):
        username_field = self.username_field
        username_val = attrs.get(username_field)

        # If looks like an email, try to resolve to a username
        if username_val and '@' in username_val:
            try:
                user = User.objects.filter(email__iexact=username_val).first()
                if user:
                    attrs[username_field] = user.get_username()
            except Exception:
                pass

        return super().validate(attrs)
