from django import forms
from django.forms import ModelForm
from .models import Follow, Comment


class RequestFollowForm(ModelForm):
    class Meta:
        model = Follow
        fields = ['user', 'follow_user', ]


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['content']