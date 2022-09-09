from django.utils.functional import SimpleLazyObject
from django.contrib.auth import get_user
from rest_framework.response import Response
from rest_framework_simplejwt import authentication
from django.contrib.auth.models import User

class MyAuditCustomMiddleware:
    #[*]DRF handles authentication in Views but Django and Django auditlog handles
    #authentication in Middleware, so this middleware track users to use in audit log

    def __init__(self, get_response):
        self.get_response = get_response
    @staticmethod
    def get_user(request):
        user = get_user(request)
        if user.is_authenticated:
            return user
        try:
            user = authentication.JWTAuthentication().authenticate(request)[0]
        except:
            pass
        return user

    def __call__(self, request):
        request.user = SimpleLazyObject(
            lambda: self.__class__.get_user(request))
        response = self.get_response(request)
        return response

