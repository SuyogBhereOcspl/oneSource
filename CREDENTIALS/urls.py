from django.urls import path
from . import views

urlpatterns = [
    path('credentials/add/', views.credential_add, name='credential_add'),
    path('credentials/view/', views.credential_list, name='credential_list'),
    path('credentials/edit/<int:pk>/', views.credential_edit, name='credential_edit'),
    path('credentials/delete/<int:pk>/', views.credential_delete, name='credential_delete'),
]
