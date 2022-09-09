from datetime import datetime
from decouple import config

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail, EmailMessage
from django.contrib.auth import get_user_model
from django.template import loader
from django.shortcuts import get_object_or_404
from django.contrib.auth.signals import user_logged_in

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ParseError, NotFound

from rest_framework_simplejwt.views import TokenObtainPairView

from drf_spectacular.utils import extend_schema, extend_schema_serializer
from drf_spectacular.types import OpenApiTypes

from backend import models

from . import serializer

from .. import utils
from ..users.serializer import UserSerializer


class Login(TokenObtainPairView):
    '''
    Login logs a user into the system
    '''
    serializer_class = serializer.LoginSerializer

    @extend_schema(responses=serializer.LoginResponseSerializer)
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        user_id = response.data.get('user')["id"]
        user = get_user_model().objects.get(pk=user_id)
        user_logged_in.send(sender=user.__class__, request=request, user=user)
        return utils.CustomResponse.Success(response.data)


class PasswordResetRequest(APIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = serializer.PasswordResetRequestSerializer

    @extend_schema(responses=OpenApiTypes.STR)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            qs = get_user_model().objects.all()
            user_email = serialized_data['Email']
            user = get_object_or_404(qs, Email=user_email)
            if not user.is_active:
                raise NotFound('This email is inactive', 'inactive_user')
            else:
                token = default_token_generator.make_token(user)
                uid = user.pk
                # create password reset object in db
                models.PasswordReset.objects.get_or_create(user_id=user.pk, token=token)

                # Use smarteye live link
                reset_link = (config('SMARTEYE_BASE_URL')+"#/auth/resetpassword/{uid}/{token}?reset=password").format(uid=uid, token=token)
                # "https://smarteye.com.au/#/auth/resetpassword/{uid}/{token}?reset=password".format(uid=uid, token=token)

                email_template_name = 'custom_email_template.html'
                template_context = {
                    "username": user.get_username,
                    "reset_link": reset_link
                }
                email = loader.render_to_string(email_template_name, template_context)

                test = send_mail(
                    subject='Smarteye account Password Reset',
                    message=email,
                    from_email='support@e360.com',
                    recipient_list=[user_email, ]
                    )

                if test>0:
                    return utils.CustomResponse.Success('Email Sent to user', status=status.HTTP_201_CREATED)
                else:
                    return utils.CustomResponse.Failure('Email not sent', status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data=serialized.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirm(APIView):
    permission_classes = ()
    authentication_classes = ()

    @extend_schema(responses=serializer.PasswordResetResponseSerializer)
    def get(self, request, *args, **kwargs):
        qs = get_user_model().objects.all()
        uid = kwargs.get('uid')
        token = kwargs.get('token')

        user = get_object_or_404(qs, pk=uid)
        if not user.is_active:
            raise NotFound('This email is inactive', 'inactive_user')
        else:
            token_valid = default_token_generator.check_token(user, token)
            if not token_valid:
                raise ParseError('Verification token is invalid or has expired!')
            reset_object = get_object_or_404(models.PasswordReset.objects.all(), user_id=uid, token=token)
            reset_object.confirmation_status = True
            reset_object.save()

            payload = {
                'user_id': user.pk,
                'message': 'Valid verification link'
            }

            return utils.CustomResponse.Success(payload)


class PasswordChange(APIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = serializer.PasswordChangeSerializer
    
    @extend_schema(responses=OpenApiTypes.STR)
    def post(self, request, *args, **kwargs):
        qs = get_user_model().objects.all()

        # serialized incoming data
        serialized = self.serializer_class(data=request.data)

        if serialized.is_valid():
            serialized_data = serialized.validated_data
            user_id = serialized_data['user_id']
            
            token = serialized_data['token']

            user = get_object_or_404(qs, pk=user_id)
            if not user.is_active:
                raise NotFound('This email is inactive', 'inactive_user')
            token_valid = default_token_generator.check_token(user, token)
            if not token_valid:
                raise ParseError('Verification token is invalid or has expired!')
            new_password = serialized_data['password']
            user.set_password(new_password)
            user.save()

            return utils.CustomResponse.Success('Password Changed successfully')
        else:
            return Response(data=serialized.errors, status=status.HTTP_400_BAD_REQUEST)