from django.urls import path
from main import views

urlpatterns = [
    path('', views.LoginPage,name='LoginPage'),
    path('indexpage/', views.indexpage, name='indexpage'),
    path('userlogout/', views.User_logout,name='userlogout'),
    path('signuppage/', views.Signup_Page, name='signuppage'),
    
]
