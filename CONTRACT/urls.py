from django.urls import path
from . import views

urlpatterns = [
    path('contract/daily-entry/', views.contract_daily_attendance_entry, name='contract_daily_attendance_entry'),
    path('contract/dailyreport/', views.contract_shiftwise_report, name='contract_shiftwise_report'),
    path('contract/daily-entry/edit/', views.contract_daily_attendance_edit, name='contract_daily_attendance_edit'),
    path('contract/shiftwise_report_excel/',views.contract_shiftwise_report_excel,name='contract_shiftwise_report_excel'),
    
    
    
    path('contract/entry/', views.contractor_worker_entry_add, name='contractor_worker_entry_add'),
    path('contract/view/', views.contractor_worker_entry_list, name='contractor_worker_entry_list'),
    path('contract/entry/edit/<str:date_str>/', views.contractor_worker_entry_edit, name='contractor_worker_entry_edit'),
    path('contractor/delete/<date_str>/', views.contractor_worker_entry_delete, name='contractor_worker_entry_delete'),
    path('contractor/view/<date_str>/', views.contractor_worker_entry_detail, name='contractor_worker_entry_detail'),

]




