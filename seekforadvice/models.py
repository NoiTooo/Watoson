from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class Seek(models.Model):
    """ アドバイスを求める """
    content = models.TextField(max_length=1000)
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.content[:15]

    class Meta:
        verbose_name = "seek"
        verbose_name_plural = "seek"


class Advice(models.Model):
    """ アドバイスをする """
    content = models.TextField(max_length=1000)
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post_connected = models.ForeignKey(Seek, on_delete=models.CASCADE)

    def __str__(self):
        return f'{str(self.author.account_name)}：{str(self.date_posted)}'

    class Meta:
        verbose_name = "advice"
        verbose_name_plural = "advice"