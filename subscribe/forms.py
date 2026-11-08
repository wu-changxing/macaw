# subscribe/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _


class SubscriberForm(forms.Form):
    # A plain form, not a ModelForm: the unique check would tell anyone
    # whether an address is already subscribed.
    email = forms.EmailField(error_messages={
        "required": _("This field is required."),
        "invalid": _("Enter a valid email address."),
    })

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()
