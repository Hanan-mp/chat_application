from django.urls import path
from chat_app import views
from django.contrib.auth import views as auth_views
urlpatterns = [
path('chat/', views.view_chat, name='chat'),
path('signup/',views.signup, name='signup'),
path('',views.login_view, name='login'),
path('logout/',views.logout_view,name="logout"),
path('create-thread/', views.create_thread, name='create_thread'),
path('mark_messages_as_read/<int:thread_id>/', views.mark_messages_as_read, name='mark_messages_as_read'),
path('chat/<int:thread_id>/', views.view_chat, name='view_chat'),




#reset password urls
path('forget_password/',views.forgot_password,name="forget_password"),
path('password_reset_sent/<str:reset_id>/',views.password_reset_sent,name="password_reset_sent"),
path('change_password/<str:reset_id>/',views.change_password,name="change_password"),
]