
from django.urls import path
from . import views

urlpatterns = [
    path('fetch-attendance/', views.fetch_attendance_from_device, name='fetch_attendance'),
     path('canteen-dashboard/', views.canteen_dashboard, name='canteen_dashboard'),
     path('attendance/', views.update_attendance, name='update_attendance'),
     path('device_push/', views.device_push, name='device_push'),
     path('api/dashboard-data/', views.dashboard_data_api, name='dashboard_data_api'),
     path('canteen-attendance-summary/', views.canteen_attendance_summary_report, name='canteen_attendance_summary_report'),
     path('download_canteen/download/', views.download_canteen_excel, name='download_canteen_excel'),

     path('attendance-list/', views.attendance_list, name='attendance_list'),
     path('attendance/xlsx/', views.attendance_xlsx,name='attendance_xlsx'),
]