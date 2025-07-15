from django import forms
from .models import Credentials

class CredentialApplicationForm(forms.ModelForm):
    class Meta:
        model = Credentials
        fields = [
            'location', 'device', 'lan_ip', 'wan_ip', 'port_no', 'frwd_to', 'url',
            'user_name', 'old_password', 'new_password', 'status', 'expiry_on'
        ]
        widgets = {
            'location': forms.Select(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
            }),
            'device': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'Device',
            }),
            'lan_ip': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'LAN IP',
                'type': 'text',
            }),
            'wan_ip': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'WAN IP',
                'type': 'text',
            }),
            'port_no': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'Port No',
            }),
            'frwd_to': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'Forward To',
            }),
            'url': forms.URLInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'URL',
            }),
            'user_name': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'User Name',
            }),
            'old_password': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'Old Password',
            }),
            'new_password': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'New Password',
            }),
            'status': forms.Select(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
            }),
            'expiry_on': forms.DateInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'type': 'date',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False
