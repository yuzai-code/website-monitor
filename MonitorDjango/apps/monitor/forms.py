from django import forms
from .models import LogFileModel, WebsiteModel


class LogFileForm(forms.ModelForm):
    website = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter website URL here'}), required=False)

    class Meta:
        model = LogFileModel
        fields = ('upload_file', 'website', 'nginx_log_format')

    def clean_website(self):
        website_url = self.cleaned_data.get('website')
        if website_url:
            website, created = WebsiteModel.objects.get_or_create(domain=website_url)
            return website
        else:
            raise forms.ValidationError("This field is required.")
