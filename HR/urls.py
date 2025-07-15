
from django.urls import path
from HR import views



urlpatterns = [
    path('create_hr/', views.create_hr, name='create_hr'),
    path('view_hr_records/', views.view_hr_records, name='view_hr_records'),
    path('edit_hr/<int:pk>/', views.edit_hr, name='edit_hr'),
    path('delete_hr/<int:pk>/', views.delete_hr, name='delete_hr'),


    path('attendance/summary/', views.attendance_summary, name='attendance_summary'),
    path('attendance/summary/<str:status_code>/', views.attendance_by_status, name='attendance_by_status'),
    path('attendance/download_excel/<path:status_code>/', views.attendance_download_excel, name='attendance_download_excel'),


    path('attendance/regulation/summary/', views.attendance_regulation_summary, name='attendance_regulation_summary'),
    path('attendance/regulation/<str:status>/', views.attendance_regulation_by_status, name='attendance_regulation_by_status'),
    path('attendance-regulation-download/<str:status>/', views.download_attendance_regulation_excel, name='download_attendance_regulation_excel'),


    path('daily-check-in-summary/', views.daily_check_in_summary, name='daily_check_in_summary'),
    path('check-in-status/<str:check_in_status>/', views.check_in_status_detail, name='check_in_status_detail'),
    path('check-in/excel/<str:check_in_status>/',views.check_in_status_excel_download,name='check_in_status_excel_download'),

    path('late-early-go-summary/', views.late_early_go_summary, name='late_early_go_summary'),
    path('late-early-go-detail/<str:late_early>/', views.late_early_go_detail, name='late_early_go_detail'),
    path('late-early-go-download/<str:late_early>/', views.late_early_go_download_excel, name='late_early_go_download_excel'),


    path('on-duty-request-summary/', views.on_duty_request_summary, name='on_duty_request_summary'),
    path('on-duty-request-detail/<str:request_status>/', views.on_duty_request_detail, name='on_duty_request_detail'),
    path('on-duty-request-download/<str:request_status>/', views.on_duty_request_download_excel, name='on_duty_request_download'),


    path('attendance_report/', views.attendance_report, name='attendance_report'),

    path('overtime-report-summary/', views.overtime_report_summary, name='overtime_report_summary'),
    path('overtime-report-detail/<str:request_status>/', views.overtime_report_detail, name='overtime_report_detail'),
    path('overtime-report-excel/<str:request_status>/', views.download_overtime_report_excel, name='download_overtime_report_excel'),

    
    path('short-leave-summary/', views.short_leave_summary, name='short_leave_summary'),
    path('short-leave/detail/<str:status>/', views.short_leave_detail, name='short_leave_detail'),
    path('short-leave-download/<str:status>/', views.download_short_leave_excel, name='download_short_leave_excel'),


    path('helpdesk/summary/', views.helpdesk_ticket_summary, name='helpdesk_ticket_summary'),
    path('helpdesk/detail/<str:status>/', views.helpdesk_ticket_detail, name='helpdesk_ticket_detail'),
    path('helpdesk/download/<str:status>/', views.download_helpdesk_ticket_excel, name='download_helpdesk_ticket_excel'),


    path('mis-report/', views.mis_report, name='hr_mis_report'),
    path('mis/download/', views.download_mis_report_excel, name='download_mis_report_excel'),


    path('data_display/', views.fetch_api_data, name='data_display'),

    path('attendance/pivot-report/', views.attendance_pivot_report, name='attendance_pivot_report'),
    path('pivot-report/pivot-report-excel/', views.attendance_pivot_excel, name='attendance_pivot_excel'),
]
