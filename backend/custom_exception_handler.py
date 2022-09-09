from rest_framework.views import exception_handler
from django.http import JsonResponse


def my_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Update the structure of the response data.
    if response is not None:
        customized_response = {}
        customized_response['errors'] = []
        customized_response['status'] = 'failed'
        customized_response['code'] = response.status_code
        customized_response['data'] = ''
        #exception could be a list or dict
        if isinstance(response.data, list):
            customized_response['errors'].extend(response.data)
        elif isinstance(response.data, dict):
            if 'detail' in response.data:
                customized_response['errors'].append(response.data.get('detail'))
            else:
                for key, value in response.data.items():
                    customized_response['errors'].append({key: value[0] if len(value)==1 else value})

        response.data = customized_response

    return response


def custom404(request):
    return JsonResponse({
        'code': 404,
        'errors': 'The resource was not found',
        'status': 'failed',
        'data': ''
    })
