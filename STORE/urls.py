
from django.urls import path,include
from STORE import views


urlpatterns = [
    path('search_supplier/', views.search_supplier, name='search_supplier'),
    path('search_item/', views.search_item, name='search_item'),
    path('add_vehicle/', views.add_vehicle, name='add_vehicle'),
    path('vehicle_list/', views.vehicle_list, name='vehicle_list'), 
    path('vehicle/edit/<int:vehicle_id>/', views.edit_vehicle, name='edit_vehicle'),
    path('vehicle/delete/<int:vehicle_id>/', views.delete_vehicle, name='delete_vehicle'),
    path('vehicle/view/<int:vehicle_id>/', views.view_vehicle, name='view_vehicle'),
    path('vehicles/download/', views.vehicle_download_excel, name='vehicle_download_excel'),
    path('vehicle-chart-report/', views.vehicle_chart_report, name='vehicle_chart_report'),
    path('materials/',            views.material_list,   name='material-list'),
    path('materials/new/',        views.material_create, name='material-create'),
    path('materials/<int:pk>/',   views.material_detail, name='material-detail'),
    path('materials/<int:pk>/edit/',   views.material_edit,   name='material-edit'),
    path('materials/<int:pk>/delete/', views.material_delete, name='material-delete'),
]
