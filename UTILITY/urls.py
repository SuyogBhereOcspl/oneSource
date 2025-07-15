from django.urls import path,include
from UTILITY import views

urlpatterns = [
    # new‐batch
    path("utility/entry/", views.entry_view, name="utility_entry"),
    path("utility/records/", views.utility_readings_report, name="utility_readings_report"),
    path('utility/readings_excel/', views.utility_readings_excel, name='utility_readings_excel'),
    path('utility/edit/date/<str:date_str>/', views.edit_utility_date, name='utility_entry_edit_date'),
    path('utility/delete/<str:date_str>/', views.delete_utility_date, name='utility_entry_delete_date'),
    path('utility/consumption/', views.utility_consumption_report, name='utility_consumption_report'),
    path('utility_consumption_report/export/', views.utility_consumption_excel, name='utility_consumption_excel'),
    
]
