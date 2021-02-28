from django import forms
from django.forms import ModelForm
from .models import Seek, Advice


class AddAdvice(forms.ModelForm):
    class Meta:
        model = Advice
        fields = ['content',]