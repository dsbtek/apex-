from collections import OrderedDict
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import response
from rest_framework.utils.urls import remove_query_param, replace_query_param
from .utils import CustomResponse
from decouple import config


class HeaderLimitOffsetPagination(LimitOffsetPagination):
    default_limit =  750

    def paginate_queryset(self, queryset, request, view=None):
        '''
        Allow option for envelope, default is False 
        '''
        self.use_envelope = False
        if str(request.GET.get('envelope')).lower() in ['true', '1']:
            self.use_envelope = True
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        '''
        Add metadata to header
        '''
        env = config('ENVIRONMENT')
        if env == 'local':
            next_url = self.get_next_link()
            prev_url = self.get_previous_link()
            first_url = self.get_first_link()
            last_url = self.get_last_link()
        
        else:
            next_url = str(self.get_next_link()).replace("http","https")
            prev_url = str(self.get_previous_link()).replace("http","https")
            first_url = str(self.get_first_link()).replace("http","https")
            last_url = str(self.get_last_link()).replace("http","https")
        

        links = []
        for url, label in (
            (next_url, 'next'),
            (prev_url, 'prev'),
            (first_url, 'first'),
            (last_url, 'last')
        ):
            if url is not None:
                links.append('<{}>; rel="{}"'.format(url, label))

        headers = {'X-Total-Count': self.count}
        if links:
            headers['Link'] = ', '.join(links)
        if self.use_envelope:
            data = OrderedDict([
                ('count', self.count),
                ('first', first_url),
                ('next', next_url),
                ('prev', prev_url),
                ('last', last_url),
                ('data', data)
            ])
        return data, headers

    def get_first_link(self):
        if self.offset <= 0:
            return None
        url = self.request.build_absolute_uri()
        return remove_query_param(url, self.offset_query_param)

    def get_last_link(self):
        if self.offset + self.limit >= self.count:
            return None

        url = self.request.build_absolute_uri()
        url = replace_query_param(url, self.limit_query_param, self.limit)

        offset = self.count - self.limit
        return replace_query_param(url, self.offset_query_param, offset)


class SQLHeaderLimitOffsetPagination(HeaderLimitOffsetPagination):
    def paginate_queryset(self, queryset, request, view=None):
        self.use_envelope = False
        if str(request.GET.get('envelope')).lower() in ['true', '1']:
            self.use_envelope = True
        self.count = self.get_log_count()
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None

        self.offset = self.get_offset(request)
        self.request = request
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True
        return queryset
    
    def get_log_count(self):
        return self._count
    
    def set_log_count(self, count):
        self._count = count


class LargeResultsSetPagination(HeaderLimitOffsetPagination):
    default_limit = 750

class SmallResultsSetPagination(HeaderLimitOffsetPagination):
    default_limit = 100

class SmallDefaultPagination(LimitOffsetPagination):
    #to be used on Generic API views
    default_limit = 100


class LargeDefaultPagination(LimitOffsetPagination):
    #to be used on Generic API views
    default_limit = 300