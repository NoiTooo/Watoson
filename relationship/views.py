from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic

from .models import Follow, Post, Comment, Intimate
from .forms import CommentForm

User = get_user_model()


class PostList(LoginRequiredMixin, generic.ListView):
    template_name = 'relationship/home.html'
    model = Post
    context_object_name = 'object_list'

    def queryset(self):
        """ 自分とフォローしているユーザーを取得してPost.objectを表示 """
        request_user = self.request.user
        qs = Follow.objects.filter(user=request_user)
        follows = [request_user, ]
        for user in qs:
            follows.append(user.follow_user)
        queryset = Post.objects.filter(author__in=follows).order_by('-date_posted')
        return queryset

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data()
        request_user = self.request.user
        # フォロー数をカウント
        ctx['follows_count'] = Follow.objects.filter(user=request_user).count()
        # フォロワー数をカウント
        ctx['followers_count'] = Follow.objects.filter(follow_user=request_user).count()
        return ctx


class FollowList(LoginRequiredMixin, generic.ListView):
    """ フォローリスト """
    model = Follow
    template_name = 'relationship/follow_list.html'
    context_object_name = 'objects_list'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data()
        request_user = self.request.user
        # フォローユーザーを表示
        ctx['follow_users'] = Follow.objects.filter(user=request_user)
        # フォローユーザー数をカウント
        ctx['follow_user_count'] = Follow.objects.filter(user=request_user).count()
        return ctx


class FollowerList(LoginRequiredMixin, generic.ListView):
    """ フォロワーリスト """
    model = Follow
    template_name = 'relationship/follower_list.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data()
        request_user = self.request.user
        # フォロワーユーザーを表示
        ctx['my_followers'] = Follow.objects.filter(follow_user=request_user)
        # フォロワーユーザー数をカウント
        ctx['my_followers_count'] = Follow.objects.filter(follow_user=request_user).count()
        # フォローリスト(qs)を返す
        qs = Follow.objects.filter(user=request_user)
        follow_lst = [i for i in qs]
        ctx['follower_lst'] = follow_lst
        return ctx

    def post(self, *args, **kwargs):
        """ request.method == POST """
        if self.request.method == "POST":
            # request_userを取得
            request_user = self.request.user

            # follow_request_userを取得
            follow_request_user = self.request.POST['follow']
            str_follow_request_user = str(follow_request_user)

            # フォローリストを作成
            get_user_qs = Follow.objects.filter(user=request_user)
            follow_lst = []
            for follow in get_user_qs:
                follow_lst.append(str(follow.follow_user))

            # リスト内にいなければ追加、いればスルーする
            if str_follow_request_user in follow_lst:
                pass
            else:
                my_instance = User.objects.get(account_name=request_user.account_name)
                follow_user = User.objects.get(account_name=follow_request_user)
                new = Follow(user=my_instance, follow_user=follow_user)
                new.save()
                return redirect('relationship:home')
        return self.get(self, *args, **kwargs)


class PostDetail(LoginRequiredMixin, generic.DetailView):
    """ 投稿内容の表示 """
    template_name = 'relationship/post_detail.html'
    model = Post
    context_object_name = 'objects'

    def post(self, *args, **kwargs):
        if self.request.method == "POST":
            # request_userを取得
            request_user = self.request.user

            """ フォロー機能 """
            if 'follow' in self.request.POST:

                # follow_request_userを取得
                follow_request_user = self.request.POST['follow']
                str_follow_request_user = str(follow_request_user)

                # フォローリストを作成
                get_user_qs = Follow.objects.filter(user=request_user)
                follow_lst = []
                for follow in get_user_qs:
                    follow_lst.append(str(follow.follow_user))

                # リスト内にいなければ追加、いればスルーする
                if str_follow_request_user in follow_lst:
                    pass
                else:
                    my_instance = User.objects.get(account_name=request_user.account_name)
                    follow_user = User.objects.get(account_name=follow_request_user)
                    new = Follow(user=my_instance, follow_user=follow_user)
                    new.save()
                    return redirect('relationship:home')
                return self.get(self, *args, **kwargs)

            """ コメント投稿 """
            if 'comment' in self.request.POST:
                get_form = CommentForm(self.request.POST)
                form = get_form.save(commit=False)
                form.author = request_user
                form.post_connected = Post.objects.get(pk=self.kwargs.get('pk'))
                content = {
                    'author': request_user,
                    'form': form,
                    'post_connected': Post.objects.get(pk=self.kwargs.get('pk')),
                    'comment_form': CommentForm(),
                }
            # 確認画面へ渡す
                return render(self.request, 'relationship/confirm.html', content)

            """ コメント確認画面 """
            if 'confirm' in self.request.POST:
                form = CommentForm(self.request.POST)
                commit = form.save(commit=False)
                commit.author = User.objects.get(account_name=request_user)
                commit.content = self.request.POST['content']
                commit.post_connected = Post.objects.get(content=Post.objects.get(pk=self.kwargs.get('pk')))
                if form.is_valid():
                    commit.save()
                    return redirect('relationship:post_detail', self.kwargs["pk"])
                return self.get(self, *args, **kwargs)
        return self.get(self, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        # 投稿に紐づいたコメント
        ctx['comments'] = Comment.objects.filter(post_connected=self.kwargs.get('pk'))
        # コメント投稿
        ctx['form'] = CommentForm(instance=self.request.user)
        # 自分自身
        ctx['owner'] = self.request.user.account_name
        return ctx


class PostUpdate(LoginRequiredMixin, generic.UpdateView):
    template_name = 'relationship/post_create.html'
    model = Post
    fields = ['content']
    success_url = reverse_lazy('relationship:home')

    def is_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostCreate(LoginRequiredMixin, generic.CreateView):
    model = Post
    fields = ['content']
    template_name = 'relationship/post_create.html'
    success_url = reverse_lazy('relationship:home')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class UserProfile(LoginRequiredMixin, generic.DetailView):
    model = User
    template_name = 'relationship/user_profile.html'
    context_object_name = 'objects'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data()
        """ リクエスト済みユーザーの判定 """
        # 本人と閲覧ユーザーのUser情報を取得
        user = User.objects.get(email=self.request.user)
        request_user = User.objects.get(pk=self.kwargs.get('pk'))
        # 既にリクエストしているか判定してTemplateに返す
        if Intimate.objects.filter(sender=user, receiver=request_user):
            ctx['request_done'] = True
        else:
            ctx['request_done'] = False
        # 自分自身かを判定
        if user.email == request_user.email:
            ctx['myself'] = True
        return ctx

    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            """ 承認リクエスト """
            get_sender = self.request.user
            get_receiver = self.kwargs.get('pk')
            sender_ins = User.objects.get(email=get_sender)
            receiver_ins = User.objects.get(pk=get_receiver)

            # リクエスト済みユーザーなら保存しない
            sender_qs = Intimate.objects.filter(sender=sender_ins)
            for i in sender_qs:
                if i.sender == get_sender and receiver_ins.email == str(i.receiver):
                    return self.get(self, *args, **kwargs)

            # リクエストされていたら保存しない
            receiver_qs = Intimate.objects.filter(sender=receiver_ins)
            for u in receiver_qs:
                if u.sender.email == receiver_ins.email and u.receiver == get_sender:
                    return self.get(self, *args, **kwargs)

            intimate_ins = Intimate(sender=sender_ins, receiver=receiver_ins, request=True, approval=False)
            intimate_ins.save()
            return redirect('relationship:user_profile', get_receiver)
        return self.get(self, *args, **kwargs)