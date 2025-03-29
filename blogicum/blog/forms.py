from django import forms

from .models import Post, User, Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        exclude = ['author', 'created_at']


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        exclude = ['password',
                   'last_login',
                   'is_superuser',
                   'is_staff',
                   'is_active',
                   'date_joined',
                   'groups',
                   'user_permissions']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
