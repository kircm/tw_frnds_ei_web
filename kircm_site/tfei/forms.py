import re

from django import forms
from django.core.exceptions import ValidationError


class ExportScreenNameForm(forms.Form):
    min_length = 4
    max_length = 15

    tw_user_to_export = forms.CharField(
        required=True,
        min_length=4,
        max_length=15,
        label='',
        widget=forms.TextInput(attrs={'class': 'input-text'})
    )

    def clean(self):
        cleaned_data = super().clean()
        screen_name = cleaned_data.get('tw_user_to_export')

        if len(screen_name) < self.min_length:
            raise ValidationError(f"Screen name too short (min: {self.min_length})")
        if len(screen_name) > self.max_length:
            raise ValidationError(f"Screen name too long (max: {self.max_length})")

        p = re.compile(r"^[a-zA-Z0-9_]*$")
        if not p.match(screen_name):
            raise ValidationError("Invalid screen name")


class ImportFileForm(forms.Form):
    file_to_import = forms.FileField(
        required=True,
        label='',
        max_length=100,
        widget=forms.FileInput(attrs={'class': 'input-file'})
    )
