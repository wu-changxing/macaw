# subscribe/forms.py
from django import forms


class SubscriberForm(forms.Form):
    # A plain form, not a ModelForm: the unique check would tell anyone
    # whether an address is already subscribed.
    email = forms.EmailField()

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()
