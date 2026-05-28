from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('signup', views.signup, name="signup"),
    path('signin', views.signin, name="signin"),
    path('signout', views.signout, name="logout"),
    path('add/', views.add_friend, name="add_friend"),
    path('room/<int:other_user_id>', views.room, name="room"),
    path('password_reset/', auth_views.PasswordResetView.as_view(
      template_name="registration/password_reset.html")),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path('reset/complete/', auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
  ]