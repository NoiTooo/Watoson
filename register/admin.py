from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import ugettext_lazy as _
from .models import User, UploadImage


class MyUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'account_name')


class MyUserAdmin(UserAdmin, admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password', 'account_name', 'job', 'image')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    form = MyUserChangeForm
    add_form = MyUserCreationForm
    list_display = ('email', 'account_name', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email', 'account_name', 'first_name', 'last_name')
    ordering = ('email',)


class UploadImageAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('user', 'upload_img')}),
    )
    list_display = ('user', 'upload_img')
    ordering = ('-user',)


admin.site.register(User, MyUserAdmin)
admin.site.register(UploadImage, UploadImageAdmin)