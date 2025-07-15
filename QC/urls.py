from django.urls import path
from . import views

urlpatterns = [
    path('products/',               views.product_list,            name='product_list'),
    path('products/<int:pk>/view/',     views.product_detail, name='product_detail'),
    path('products/new/',           views.product_create,          name='product_create'),
    path('products/<int:pk>/edit/', views.product_update,          name='product_update'),
    path('products/<int:pk>/delete/',views.product_delete,          name='product_delete'),
    path('products/import-appearance/', views.import_appearance_view, name='import_appearance'),
    path('products/product/<int:pk>/spec-upload/',views.import_specs,name='spec_upload'),

     # Returns JSON list of specs for a product
    path('qc/api/specs/',        views.get_specs,           name='get_specs'),
    # Returns JSON “header + specs” for a product
    path('qc/api/product-data/', views.get_product_details, name='get_product_details'),
    # ─── Dashboard / Reports ───────────────────────────────────────────────────
    # QC dashboard (if you have a landing page or overview)
    path('qc/dashboard/',        views.dashboard,           name='dashboard'),
    # QC reports list (e.g. summary page) – now uses qc_list instead of 'report'
    path('qc/reports/',          views.qc_list,             name='qc_report'),

    # ─── CRUD Views ────────────────────────────────────────────────────────────
    # List all QC entries (at /qc/)
    path('qc/home/',                views.dashboard,   name='qc_home'),

    path('qc/',                  views.qc_list,             name='qc_list'),
    # Create a new QC entry (at /qc/new/)
    path('qc/new/',              views.qc_create,           name='qc_create'),
    # Detail view for a single QC entry (at /qc/<pk>/)
    path('qc/<int:pk>/',         views.qc_detail,           name='qc_detail'),
    # Edit/update an existing QC entry (at /qc/<pk>/edit/)
    path('qc/<int:pk>/edit/',    views.qc_update,           name='qc_update'),
    # Delete confirmation and action for a QC entry (at /qc/<pk>/delete/)
    path('qc/<int:pk>/delete/',  views.qc_delete,           name='qc_delete'),
        # ─── “Reopen” Endpoints ─────────────────────────────────────────────────────
    path('qc/<int:pk>/reopen_qc/',  views.qc_reopen_for_qc,   name='qc_reopen_for_qc'),
    path('qc/<int:pk>/reopen_prod/', views.qc_reopen_for_prod, name='qc_reopen_for_prod'),
        # ── NEW: Cancel a QC entry ─────────────────────────────────────────
    path('qc/<int:pk>/cancel/',  views.qc_cancel,           name='qc_cancel'),
    # ─── Master lists ───────────────────────────────────────────────────────────
    path('qc/equipment-master/', views.equipment_master,    name='equipment_master'),
    path('qc/item-master/',      views.item_master,         name='item_master'),
    # MIS report
    path('qc/mis-report/', views.mis_report, name='mis_report'),
    
    path('sync-erp/', views.sync_erp, name='sync_erp'),
]