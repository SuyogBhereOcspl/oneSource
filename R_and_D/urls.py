from django.urls import path
from . import views

urlpatterns = [
    path('moisture/add/', views.add_r_and_d_moisture, name='add_r_and_d_moisture'),
    path('moisture/<int:pk>/edit/', views.edit_r_and_d_moisture, name='edit_r_and_d_moisture'),
    path('moisture/', views.r_and_d_moisture_list, name='r_and_d_moisture_list'),
    path('moisture/<int:pk>/delete/', views.delete_r_and_d_moisture, name='delete_r_and_d_moisture'),
    path('r_and_d_moisture/download_xlsx/', views.r_and_d_moisture_download_xlsx, name='r_and_d_moisture_download_xlsx'),

    path('kfactor/add/', views.add_kf_factor_entry, name='add_kf_factor_entry'),
    path('kfactor/list/', views.kf_factor_entry_list, name='kf_factor_entry_list'),

]
