from django.urls import path
from ETP import views

urlpatterns = [
    path('add-effluent/', views.add_effluent_record, name='add_effluent_record'),

    path('get_products/', views.get_products, name='get_products'),
    path('get_stage_names/', views.get_stage_names, name='get_stage_names'),
    path('get_batch_nos/', views.get_batch_nos, name='get_batch_nos'),
    path('get_voucher_details_by_batch/', views.get_voucher_details_by_batch, name='get_voucher_details_by_batch'),
    path('get_effluent_qty_details/', views.get_effluent_qty_details, name='get_effluent_qty_details'),

        
    path('add-effluent/', views.add_effluent_record, name='add_effluent_record'),
    path('view-effluent-records/', views.effluent_records_list, name='view_effluent_records'),
    path('effluent/<int:pk>/edit/', views.edit_effluent_record, name='edit_effluent_record'),
    path('effluent/qty/<int:qty_id>/delete/', views.delete_effluent_qty, name='delete_effluent_qty'),
    path('download-effluent-excel/', views.download_effluent_excel, name='download_effluent_excel'),
    path('effluent/report/', views.effluent_plan_actual_report, name='effluent_plan_actual_report'),

    

    path('add-general-effluent/', views.add_general_effluent, name='add_general_effluent'),
    path('view-general-effluent/', views.view_general_effluent_records, name='view_general_effluent'),
    path('edit-general-effluent/<int:pk>/', views.edit_general_effluent, name='edit_general_effluent'),
    path('general-effluent/delete/<int:pk>/', views.delete_general_effluent, name='delete_general_effluent'),
    path('general-effluent/chart/', views.general_effluent_charts, name='general_effluent_charts'),
]
# 