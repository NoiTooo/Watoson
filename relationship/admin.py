from django.contrib import admin
from .models import Follow, Post, Comment, Intimate

admin.site.register(Follow)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Intimate)
