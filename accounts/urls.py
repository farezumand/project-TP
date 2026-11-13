from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_register, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
