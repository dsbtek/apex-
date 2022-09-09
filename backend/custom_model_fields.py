from django.core import validators
from django.db import models
import re


class EmailListField(models.TextField):

    def to_python(self, value):

        if not value:
            return None  # []

        cleaned_email_list = list()
        #email_list = filter(None, value.split(','))
        email_list = filter(None, re.split(r';|,\s|\n', value))

        for email in email_list:
            if email.strip(' @;,'):
                cleaned_email_list.append(email.strip(' @;,'))

        cleaned_email_list = list(set(cleaned_email_list))

        return ", ".join(cleaned_email_list)

    def validate(self, value, model_instance):
        """Check if value consists only of valid emails."""

        # Use the parent's handling of required fields, etc.
        super(MultiEmailField, self).validate(value, model_instance)

        email_list = value.split(',')

        for email in email_list:
            validate_email(email.strip())