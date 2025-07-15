from django.urls import path
from EHS import views

urlpatterns = [
    path('add-physical-location/', views.add_physical_location, name='add_physical_location'),
    path('add_leading_record/', views.add_leading_record, name='add_leading_record'),
    path('view_leading/', views.view_leading_records, name='view_leading'),
    path('leading/<int:pk>/detail/', views.leading_record_detail, name='leading_record_detail'),
    path('leading/<int:pk>/edit/', views.edit_leading_record, name='edit_leading_record'),
    path('leading/<int:pk>/delete/', views.delete_leading_record, name='delete_leading_record'),
    path('leading/export/', views.export_leading_excel, name='export_leading_excel'),
    path('leading/leading-chart-summary/', views.leading_chart_summary, name='leading_chart_summary'),

    path('add_lagging_indicator/', views.add_lagging_indicator, name='add_lagging_indicator'),
    path('lagging-records/', views.view_lagging_records, name='view_lagging'),
    path('lagging-records/<int:record_id>/', views.lagging_record_detail, name='lagging_record_detail'),
    path('lagging/edit/<int:record_id>/', views.edit_lagging_indicator, name='edit_lagging_record'),
    path('lagging/delete/<int:record_id>/', views.delete_lagging_record, name='delete_lagging_record'),
    path('download-lagging-excel/', views.download_lagging_excel, name='download_lagging_excel'),
    path('lagging/lagging-chart-summary/', views.lagging_chart_summary, name='lagging_chart_summary'),

    path('pssr/add/', views.add_pssr_record, name='add_pssr_record'),
    path('pssr/edit/<int:record_id>/', views.edit_pssr_record, name='edit_pssr_record'),
    path('pssr/list/', views.pssr_record_list, name='pssr_record_list'),
    path("pssr/<int:pk>/",      views.pssr_record_detail, name="pssr_record_detail"),
    path("pssr/download/", views.download_pssr_excel, name="download_pssr_excel"),
    path('pssr/delete/<int:record_id>/',views.delete_pssr_record,name='delete_pssr_record'),
    path("pssr/observation/<int:pk>/delete/", views.delete_pssr_observation,name="delete_pssr_observation"),
    path('pssr/pssr-chart-summary/', views.pssr_chart_summary, name='pssr_chart_summary'),
    
]
