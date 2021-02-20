import hashlib
import os
from datetime import datetime

from django.db import models
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from PIL import Image


class CustomUserManager(UserManager):
    """ユーザーマネージャー"""
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


def user_img_upload_to(instance, filename):
    """ User:画像名をハッシュを用いてリネームし保存する """
    current_time = datetime.now()
    pre_hash_name = f'{instance.account_name}{filename}{current_time}'
    extension = str(filename).split('.')[-1]
    hs_filename = f'{instance.pk}_{hashlib.md5(pre_hash_name.encode()).hexdigest()}.{extension}'
    saved_path = 'media/profile_pics/'
    return f'{saved_path}{hs_filename}'


def validate_is_picture(value):
    """ 画像の拡張子を指定するバリデーション """
    ext = os.path.splitext(value.name)[1]

    if not ext.lower() in ['.jpg', '.png', '.jpeg']:
        raise ValidationError('「.jpg」・「.png」。「jpeg」のみ可能です」')


class User(AbstractBaseUser, PermissionsMixin):
    """カスタムユーザーモデル:emailアドレスをユーザー名として使う"""
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    account_name = models.CharField(_('account name'), unique=True, blank=True, null=True, max_length=30)
    image = models.ImageField(default='media/profile_pics/default.jpg', upload_to=user_img_upload_to, validators=[validate_is_picture])
    job = models.CharField(max_length=30, null=True, blank=True,)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_(
            'Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )

    objects = CustomUserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in
        between."""
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def save(self, *args, **kwargs):
        """ 画像のリサイズ """
        super().save()
        img = Image.open(self.image.path)
        if img.height > 200 or img.width > 200:
            output_size = (200, 200)
            img.thumbnail(output_size)
            img.save(self.image.path)

    @property
    def username(self):
        return self.email


def user_img_upload_to(instance, filename):
    """ UploadImage:画像名をハッシュを用いてリネームし保存する """
    current_time = datetime.now()
    pre_hash_name = f'{filename}{current_time}'
    extension = str(filename).split('.')[-1]
    hs_filename = f'{instance.pk}_{hashlib.md5(pre_hash_name.encode()).hexdigest()}.{extension}'
    saved_path = 'media/profile_pics/'
    return f'{saved_path}{hs_filename}'


class UploadImage(models.Model):
    """ アップロード画像 """
    user = models.OneToOneField(User, related_name='upload', on_delete=models.CASCADE)
    upload_img = models.ImageField(default='media/profile_pics/default.jpg', upload_to=user_img_upload_to, validators=[validate_is_picture])

    class Meta:
        verbose_name = "profile_image_upload"
        verbose_name_plural = "ProfileImageUpload"

    def save(self, *args, **kwargs):
        """ 画像のリサイズ """
        super().save()
        img = Image.open(self.upload_img.path)
        if img.height > 200 or img.width > 200:
            output_size = (200, 200)
            img.thumbnail(output_size)
            img.save(self.upload_img.path)

    def __str__(self):
        return str(self.user)