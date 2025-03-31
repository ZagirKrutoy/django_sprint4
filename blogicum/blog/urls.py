from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.IndexListView.as_view(), name="index"),
    path(
        "posts/<int:pk>/",
        views.PostDetailView.as_view(),
        name="post_detail"),
    path("category/<slug:category_slug>/",
         views.CategoryPostListView.as_view(),
         name="category_posts"),
    path('error/', views.trigger_error),
    path('forbidden/', views.trigger_403),
    path('profile/<str:username>/',
         views.ProfileView.as_view(), name='profile'),
    path('profile/edit',
         views.EditProfileView.as_view(), name='edit_profile'),
    path('posts/create/', views.CreatePostView.as_view(), name='create_post'),
    path('posts/<int:pk>/delete',
         views.PostDeleteView.as_view(),
         name='delete_post'),
    path('posts/<int:pk>/edit/',
         views.EditDeleteView.as_view(),
         name='edit_post'),
    path('posts/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('posts/<int:pk>/edit_comment/<int:comment_id>',
         views.edit_comment,
         name='edit_comment'),
    path('posts/<int:pk>/delete_comment/<int:comment_id>/',
         views.delete_comment,
         name='delete_comment'),
]
