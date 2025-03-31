from django.utils.timezone import now
from django.views.generic import (ListView,
                                  DetailView,
                                  CreateView,
                                  UpdateView,
                                  DeleteView)
from .models import Post, Category, Comment
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from .forms import PostForm, UserForm, CommentForm
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import UserPassesTestMixin


class IndexListView(ListView):
    model = Post
    template_name = "blog/index.html"
    context_object_name = "post_list"
    queryset = Post.objects.filter(
        pub_date__lte=now(),
        is_published__exact=True,
        category__is_published=True,
    ).order_by('-pub_date')
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for post in context["post_list"]:
            post.comment_count = post.comment_count()
        return context


'''def index(request):
    template_name = "blog/index.html"
    inverted_posts = list(reversed(posts))
    return render(request, template_name, {"posts": inverted_posts})'''


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return Post.objects.filter(
            pub_date__lte=now(),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Записываем в переменную form пустой объект формы.
        context['form'] = CommentForm()
        # Запрашиваем все поздравления для выбранного дня рождения.
        context['comments'] = (
            # Дополнительно подгружаем авторов комментариев,
            # чтобы избежать множества запросов к БД.
            self.object.comments.select_related('author')
        )
        return context


'''def post_detail(request, id):
    template_name = "blog/detail.html"
    post = next((post for post in posts if post["id"] == id), None)

    return render(request, template_name, {"post": post})'''


class CategoryPostListView(ListView):
    model = Post
    template_name = "blog/category.html"
    context_object_name = "post_list"
    paginate_by = 10

    def get_queryset(self):
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True)
        return Post.objects.filter(
            category=category,
            is_published=True,
            pub_date__lte=now()
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True)
        return context


'''def category_posts(request, category_slug):
    template_name = "blog/category.html"
    return render(request, template_name, {"category": category_slug})'''


class ProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        posts = Post.objects.filter(author=user).order_by('-pub_date')
        paginator = Paginator(posts, 10)  # 5 публикаций на страницу
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        return context


@method_decorator(login_required, name='dispatch')
class EditProfileView(UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user.username})


@login_required
def change_password(request):
    return render(request, 'registration/password_change_form.html')


@method_decorator(login_required, name='dispatch')
class CreatePostView(CreateView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm

    def form_valid(self, form):
        # Устанавливаем текущего пользователя как автора
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})


class PostDeleteView(UserPassesTestMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('blog:index') 

    def test_func(self):
        post = self.get_object()
        return (
            self.request.user == post.author
            or self.request.user.is_superuser)

    def handle_no_permission(self):
        return redirect('blog:post_detail', pk=self.get_object().pk)


class EditDeleteView(UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            # Если пользователь не автор, перенаправляем на страницу поста
            return redirect('blog:post_detail', pk=post.pk)
        return super().dispatch(request, *args, **kwargs)


@login_required
def add_comment(request, pk):
    # Получаем объект дня рождения или выбрасываем 404 ошибку.
    post = get_object_or_404(Post, pk=pk)
    # Функция должна обрабатывать только POST-запросы.
    form = CommentForm(request.POST)
    if form.is_valid():
        # Создаём объект поздравления, но не сохраняем его в БД.
        comment = form.save(commit=False)
        # В поле author передаём объект автора поздравления.
        comment.author = request.user
        # В поле birthday передаём объект дня рождения.
        comment.post = post
        # Сохраняем объект в БД.
        comment.save()
    # Перенаправляем пользователя назад, на страницу.
    return redirect('blog:post_detail', pk=pk)


@login_required
def edit_comment(request, pk, comment_id):
    post = get_object_or_404(Post, pk=pk)
    # Получаем комментарий или выбрасываем 404 ошибку
    comment = get_object_or_404(Comment, pk=comment_id, post_id=pk)
    # Проверяем, что только автор может редактировать
    if comment.author != request.user:
        return redirect('blog:post_detail', pk=pk)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', pk=pk)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment,
        'post': post
    })


@login_required
def delete_comment(request, pk, comment_id):
    # Получаем комментарий или выбрасываем 404 ошибку
    comment = get_object_or_404(Comment, pk=comment_id, post_id=pk)
    # Проверяем, что только автор может удалять
    if comment.author != request.user:
        return redirect('blog:post_detail', pk=pk)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', pk=pk)

    return render(request, 'blog/comment.html', {'comment': comment})


def trigger_error(request):
    1 / 0


def trigger_403(request):
    raise PermissionDenied
