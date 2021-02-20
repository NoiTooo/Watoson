from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.http import HttpResponseBadRequest, Http404
from django.shortcuts import redirect, resolve_url, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import generic

from project.settings import DEFAULT_FROM_EMAIL
from relationship.models import Intimate

from .models import UploadImage
from .forms import (
    LoginForm, UserCreateForm, UserUpdateForm, MyPasswordChangeForm,
    MyPasswordResetForm, MySetPasswordForm, EmailChangeForm, UploadImageForm
)

User = get_user_model()


class Top(generic.TemplateView):
    template_name = 'register/top.html'


class Login(LoginView):
    """ログインページ"""
    form_class = LoginForm
    template_name = 'register/login.html'


class Logout(LogoutView):
    """ログアウトページ"""
    template_name = 'register/top.html'


class UserCreate(generic.CreateView):
    """ユーザー仮登録"""
    template_name = 'register/user_create.html'
    form_class = UserCreateForm

    def form_valid(self, form):
        """仮登録と本登録用メールの発行."""
        # 仮登録と本登録の切り替えは、is_active属性を使うと簡単です。
        # 退会処理も、is_activeをFalseにするだけにしておくと捗ります。
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # アクティベーションURLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': domain,
            'token': dumps(user.pk),
            'user': user,
        }

        subject = render_to_string('register/mail_template/create/subject.txt', context)
        message = render_to_string('register/mail_template/create/message.txt', context)

        # 編集
        send_mail(
            subject,
            message,
            DEFAULT_FROM_EMAIL,
            [user.email],
        )
        return redirect('register:user_create_done')


class UserCreateDone(generic.TemplateView):
    """ユーザー仮登録完了"""
    template_name = 'register/user_create_done.html'


class UserCreateComplete(generic.TemplateView):
    """メール内URLアクセス後のユーザー本登録"""
    template_name = 'register/user_create_complete.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60 * 60 * 24)  # デフォルトでは1日以内

    def get(self, request, **kwargs):
        """tokenが正しければ本登録."""
        token = kwargs.get('token')
        try:
            user_pk = loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
            return HttpResponseBadRequest()

        # tokenは問題なし
        else:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                return HttpResponseBadRequest()
            else:
                if not user.is_active:
                    # まだ仮登録で、他に問題なければ本登録とする
                    user.is_active = True
                    user.save()
                    return super().get(request, **kwargs)
            finally:
                # 画像アップロード用インスタンスを自動生成しとく
                upload_user_ins = UploadImage(user=user)
                upload_user_ins.save()

        return HttpResponseBadRequest()


class OnlyYouMixin(UserPassesTestMixin):
    """本人か、スーパーユーザーだけユーザーページアクセスを許可する"""
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return user.pk == self.kwargs['pk'] or user.is_superuser


class UserDetail(OnlyYouMixin, generic.DetailView):
    """ユーザーの詳細ページ"""
    model = User
    template_name = 'register/user_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        request_user = self.request.user
        """ あなたの承認待ちユーザーリスト """
        ctx['approval_pending_list'] = Intimate.objects.filter(receiver=request_user,
                                                               request=True, approval=False).exclude(reject=True)

        """ 相手の承認待ちユーザーリスト """
        ctx['request_list'] = Intimate.objects.filter(sender=request_user,
                                                      request=True, approval=False)

        """ 親しい友達リスト """
        intimate_qs1 = Intimate.objects.filter(sender=request_user, request=True, approval=True)
        intimate_qs2 = Intimate.objects.filter(receiver=request_user, request=True, approval=True)
        intimate_dic = {}
        for user in intimate_qs1:
            intimate_dic[(str(user.receiver.account_name))] = user.date
        for user in intimate_qs2:
            intimate_dic[str(user.sender.account_name)] = user.date
        # 繋がった日付でソート
        intimate_dic_sorted = sorted(intimate_dic.items(), key=lambda x: x[1])
        ctx['intimate_dic_sorted'] = intimate_dic_sorted

        """ 拒否したユーザーリスト """
        ctx['reject_lst'] = Intimate.objects.filter(receiver=request_user, reject=True)

        """ upload_image用 """
        upload_img = UploadImage.objects.get(user=request_user)
        ctx['upload_user_pk'] = upload_img.pk
        return ctx

    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            request_user = self.request.user
            now = datetime.now()

            """ リクエストを承認する """
            if 'approval' in self.request.POST:
                sender_user = self.request.POST['approval']
                # sender と recieverを取得
                request_user_ins = User.objects.get(email=request_user)
                sender_user_ins = User.objects.get(account_name=sender_user)
                # それぞれUserインスタンスを取得し、approval：True、date：承認した時間を保存する
                intimate_ins = Intimate.objects.get(sender=sender_user_ins, receiver=request_user_ins)
                intimate_ins.approval = True
                intimate_ins.reject = False
                intimate_ins.date = now
                intimate_ins.save()

            """ リクエストを拒否する(拒否通知はしない) """
            if 'reject' in self.request.POST:
                reject_user = self.request.POST['reject']
                # それぞれUserインスタンスを取得し、reject：Trueで保存する
                request_user_ins = User.objects.get(email=request_user)
                reject_user_ins = User.objects.get(account_name=reject_user)
                intimate_ins = Intimate.objects.get(sender=reject_user_ins, receiver=request_user_ins)
                intimate_ins.reject = True
                intimate_ins.save()
                return self.get(self, *args, **kwargs)

            """ リクエストを取り消す """
            if 'cancel' in self.request.POST:
                cancel_user = self.request.POST['cancel']
                # それぞれUserインスタンスを取得し、reject：Trueで保存する
                request_user_ins = User.objects.get(email=request_user)
                cancel_user_ins = User.objects.get(account_name=cancel_user)
                intimate_ins = Intimate.objects.get(sender=request_user_ins, receiver=cancel_user_ins)
                intimate_ins.request = False
                intimate_ins.save()

            """ 画像を取り消す """
            if 'delete' in self.request.POST:
                user_ins = User.objects.get(pk=request_user.pk)
                user_ins.image = 'media/profile_pics/default.jpg'
                user_ins.save()

            return self.get(self, *args, **kwargs)


class UserUpdate(OnlyYouMixin, generic.UpdateView):
    """ユーザー情報更新ページ"""
    model = User
    form_class = UserUpdateForm
    template_name = 'register/user_form.html'

    def get_success_url(self):
        return resolve_url('register:user_detail', pk=self.kwargs['pk'])


class UpdateImage(LoginRequiredMixin, generic.UpdateView):
    """プロフィール画像アップロード"""
    model = UploadImage
    form_class = UploadImageForm
    template_name = 'register/module/upload_image_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        user = User.objects.get(pk=self.request.user.pk)
        ctx['current_img'] = user.image
        return ctx

    def get_success_url(self):
        upload_user = UploadImage.objects.get(user=self.request.user)
        upload_user_pk = upload_user.pk
        return resolve_url('register:confirm_image', pk=upload_user_pk)

    def post(self, *args, **kwargs):
        if self.request.method == 'POST' and 'back' in self.request.POST:
            return redirect('register:user_detail', pk=self.request.user.pk)
        return super().post(self.request, *args, **kwargs)


class ConfirmImage(LoginRequiredMixin, generic.DetailView):
    """ユーザープロフィール画像確認"""
    model = User
    template_name = 'register/module/confirm_user_img.html'
    context_object_name = 'objects'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        user = UploadImage.objects.get(user=self.request.user)
        ctx['post_img'] = user.upload_img
        return ctx

    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            if 'done' in self.request.POST:
                user = UploadImage.objects.get(user=self.request.user)
                user_ins = User.objects.get(pk=self.request.user.pk)
                user_ins.image = user.upload_img
                user_ins.save()
                return redirect('register:user_detail', pk=self.request.user.pk)
            if 'back' in self.request.POST:
                return redirect('register:upload_image', pk=self.request.user.pk)
            return Http404("Error")


class PasswordChange(PasswordChangeView):
    """パスワード変更ビュー"""
    form_class = MyPasswordChangeForm
    success_url = reverse_lazy('register:password_change_done')
    template_name = 'register/password_change.html'


class PasswordChangeDone(PasswordChangeDoneView):
    """パスワード変更しました"""
    template_name = 'register/password_change_done.html'


class PasswordReset(PasswordResetView):
    """パスワード変更用URLの送付ページ"""
    subject_template_name = 'register/mail_template/password_reset/subject.txt'
    email_template_name = 'register/mail_template/password_reset/message.txt'
    template_name = 'register/password_reset_form.html'
    form_class = MyPasswordResetForm
    success_url = reverse_lazy('register:password_reset_done')


class PasswordResetDone(PasswordResetDoneView):
    """パスワード変更用URLを送信"""
    template_name = 'register/password_reset_done.html'


class PasswordResetConfirm(PasswordResetConfirmView):
    """新パスワード入力ページ"""
    form_class = MySetPasswordForm
    success_url = reverse_lazy('register:password_reset_complete')
    template_name = 'register/password_reset_confirm.html'


class PasswordResetComplete(PasswordResetCompleteView):
    """新パスワード設定完了ページ"""
    template_name = 'register/password_reset_complete.html'


class EmailChange(LoginRequiredMixin, generic.FormView):
    """メールアドレスの変更"""
    template_name = 'register/email_change_form.html'
    form_class = EmailChangeForm

    def form_valid(self, form):
        user = self.request.user
        new_email = form.cleaned_data['email']

        # URLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': domain,
            'token': dumps(new_email),
            'user': user,
        }

        subject = render_to_string('register/mail_template/email_change/subject.txt', context)
        message = render_to_string('register/mail_template/email_change/message.txt', context)
        send_mail(subject, message, None, [new_email])

        return redirect('register:email_change_done')


class EmailChangeDone(LoginRequiredMixin, generic.TemplateView):
    """メールアドレスの変更メールを送信完了"""
    template_name = 'register/email_change_done.html'


class EmailChangeComplete(LoginRequiredMixin, generic.TemplateView):
    """リンクを踏んだ後に呼ばれるメアド変更ビュー"""
    template_name = 'register/email_change_complete.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60 * 60 * 24)  # デフォルトでは1日以内

    def get(self, request, **kwargs):
        token = kwargs.get('token')
        try:
            new_email = loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
            return HttpResponseBadRequest()

        # tokenは問題なし
        else:
            User.objects.filter(email=new_email, is_active=False).delete()
            request.user.email = new_email
            request.user.save()
            return super().get(request, **kwargs)
