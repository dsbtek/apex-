from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
 
from ..users.serializer import UserSerializer

#import models
from ..models import PasswordReset, User


class LoginSerializer(TokenObtainPairSerializer):
    '''
    DRF simple-jwt does not update user last login after getting a new token.
    Fix is to subclass the TokenObtainPairSerializer and add the user_id to the
    serializer response data
    '''
    def validate(self, attrs):
        data = super(LoginSerializer, self).validate(attrs)
        data.update({'user': UserSerializer(self.user).data})
        data['token'] = data['access']
        del data['access']
        del data['refresh']
        return data


class LoginResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    token = serializers.CharField()


class PasswordChangeSerializer(serializers.Serializer):
    '''
        PasswordChangeSerializer to enable serializer on drf-spectacular
    '''
    user_id = serializers.IntegerField(required=True)
    token = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

class PasswordChangeResponseSerializer(serializers.Serializer):
    '''
        PasswordChangeSerializer to enable serializer on drf-spectacular
    '''
    user_id = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    Email = serializers.CharField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
        PasswordResetRequestSerializer to enable serializer on drf-spectacular
    """
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)

class PasswordResetResponseSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user'
    )
    message = serializers.CharField()