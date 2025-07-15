import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect,get_object_or_404
from django.http import JsonResponse,HttpResponse
from STORE.forms import VehicleForm
from  STORE .models import Vehicle
from django.db import connections
from django.contrib import messages  # Import messages framework
import pandas as pd
from django.db.models import Sum, F,Count
from calendar import monthrange
from datetime import date
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,   #  ←  this is what was missing
    ListView,
    DetailView,
    UpdateView,
    DeleteView,
)
from .models import MaterialRequest
from .forms  import MaterialRequestForm
# Initialize custom logger
logger = logging.getLogger('custom_logger')


def search_supplier(request):
    query = request.GET.get('term', '')
    logger.debug(f"Searching suppliers with term: '{query}'")

    sql_query = """
        SELECT DISTINCT SUPP.sName 
        FROM TXNHDR HDR
        LEFT JOIN BUSMST AS SUPP ON HDR.lAccId1 = SUPP.lId
        WHERE HDR.ltypid IN (
            400, 509, 520, 524, 750, 751, 752, 753, 
            754, 755, 756, 757, 758, 759, 760, 761, 
            762, 763, 764, 765, 766, 767, 768, 769, 956
        ) AND SUPP.sName LIKE %s
    """

    with connections['readonly_db'].cursor() as cursor:
        cursor.execute(sql_query, [f'%{query}%'])
        results = cursor.fetchall()

    # print("Supplier Results:", results)  # Debugging line

    suppliers = [{'id': row[0], 'text': row[0]} for row in results]
    logger.info(f"Found {len(suppliers)} suppliers for search '{query}'")
    return JsonResponse(suppliers, safe=False)


def search_item(request):
    query = request.GET.get('term', '')
    logger.debug(f"Searching items with term: '{query}'")
    sql_query = """
        SELECT DISTINCT ITM.sName 
        FROM TXNHDR HDR
        INNER JOIN TXNDET AS DET ON HDR.lId = DET.lId
        INNER JOIN ITMMST AS ITM ON DET.lItmId = ITM.lId
        WHERE HDR.ltypid IN (
            400, 509, 520, 524, 750, 751, 752, 753, 
            754, 755, 756, 757, 758, 759, 760, 761, 
            762, 763, 764, 765, 766, 767, 768, 769, 956)
			AND DET.lItmTyp IN (57, 66, 77, 60) AND ITM.sName LIKE %s
    """

    with connections['readonly_db'].cursor() as cursor:
        cursor.execute(sql_query, [f'%{query}%'])
        results = cursor.fetchall()

    # print("Item Results:", results)  # Debugging line

    items = [{'id': row[0], 'text': row[0]} for row in results]
    logger.info(f"Found {len(items)} items for search '{query}'")
    return JsonResponse(items, safe=False)



@login_required
def add_vehicle(request):
    user_groups = request.user.groups.values_list('name', flat=True)  # Check if the user is in STORE group
    is_superuser = request.user.is_superuser

    if not request.user.has_perm('STORE.add_vehicle'):
        logger.warning(f"Unauthorized add_vehicle access by user: {request.user.username}")
        messages.error(request, "You do not have permission to add vehicle records.")
        return redirect('indexpage')
        
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        try:
            if form.is_valid():
                form.save()
                logger.info(f"Vehicle added by user: {request.user.username}")
                messages.success(request, "Vehicle entry saved successfully!")
                return redirect('add_vehicle')
            else:
                messages.error(request, "Please fill in the required fields.")
                logger.warning(f"Invalid vehicle form submitted by {request.user.username}")
        except Exception as e:
            logger.exception(f"Error while saving vehicle form by {request.user.username}")
            messages.error(request, "An error occurred while saving the vehicle entry.")

    else:
        form = VehicleForm()
    return render(request, 'store/add_vehicle_form.html', locals())



@login_required
def vehicle_list(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser

    if not request.user.has_perm('STORE.view_vehicle'):
        logger.warning(f"Unauthorized vehicle_list access by user: {request.user.username}")
        messages.error(request, "You do not have permission to view vehicle records.")
        return redirect('indexpage')

    can_edit_vehicle = request.user.has_perm('STORE.change_vehicle')
    can_delete_vehicle = request.user.has_perm('STORE.delete_vehicle')
    can_add_vehicle = request.user.has_perm('STORE.add_vehicle')
    can_view_vehicle = request.user.has_perm('STORE.view_vehicle')

    filters = {
        'reporting_date': request.GET.get('reporting_date', ''),
        'name_of_supplier': request.GET.get('name_of_supplier', ''),
        'material': request.GET.get('material', ''),
        'name_of_transporter': request.GET.get('name_of_transporter', ''),
        'status': request.GET.get('status', ''),
    }

    vehicles = Vehicle.objects.all().order_by('-reporting_date')

    for key, value in filters.items():
        if value:
            vehicles = vehicles.filter(**{f"{key}__icontains": value})


    # Pagination
    paginator = Paginator(vehicles, 10)  # 10 records per page
    page = request.GET.get('page')

    try:
        vehicles_paginated = paginator.page(page)
    except PageNotAnInteger:
        vehicles_paginated = paginator.page(1)
    except EmptyPage:
        vehicles_paginated = paginator.page(paginator.num_pages)

    context = {
        'vehicles': vehicles_paginated,
        **filters,
        'user_groups': user_groups,
        'is_superuser': is_superuser,
        'can_edit_vehicle': can_edit_vehicle,
        'can_delete_vehicle': can_delete_vehicle,
        'can_add_vehicle': can_add_vehicle,
        'can_view_vehicle': can_view_vehicle,
    }
    logger.info(f"Vehicle list viewed by {request.user.username} with filters: {filters}")
    return render(request, 'store/vehicle_list.html', context)

@login_required
def edit_vehicle(request, vehicle_id):
    user_groups = request.user.groups.values_list('name', flat=True)  # Check if the user is in HR group
    is_superuser = request.user.is_superuser

    """ Edit vehicle details (Permission Required: STORE.change_vehicle) """
    if not request.user.has_perm('STORE.change_vehicle'):
        logger.warning(f"Unauthorized edit attempt by {request.user.username} on vehicle ID {vehicle_id}")
        messages.error(request, "You do not have permission to edit vehicle records.")
        return redirect('indexpage')

    try:
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    except Exception as e:
        logger.exception(f"Vehicle ID {vehicle_id} not found for editing by {request.user.username}")
        messages.error(request, "Vehicle not found.")
        return redirect('vehicle_list')
    
    if request.method == "POST":
        try:
            form = VehicleForm(request.POST, instance=vehicle)
            if form.is_valid():
                form.save()
                logger.info(f"Vehicle ID {vehicle_id} edited by {request.user.username}")
                messages.success(request, "Vehicle details updated successfully!")
                return redirect('vehicle_list')
        except Exception as e:
            logger.exception(f"Error while updating vehicle ID {vehicle_id} by {request.user.username}")
            messages.error(request, "An error occurred while updating the vehicle.")
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, 'store/edit_vehicle.html', locals())

@login_required
def delete_vehicle(request, vehicle_id):
    user_groups = request.user.groups.values_list('name', flat=True)  # Check if the user is in HR group
    is_superuser = request.user.is_superuser

    """ Delete a vehicle entry (Permission Required: STORE.delete_vehicle) """
    if not request.user.has_perm('STORE.delete_vehicle'):
        logger.warning(f"Unauthorized delete attempt by {request.user.username} on vehicle ID {vehicle_id}")
        messages.error(request, "You do not have permission to delete vehicle records.")
        return redirect('indexpage')

    if request.method == "POST":  # Ensuring deletion via POST request
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        vehicle.delete()
        logger.info(f"Vehicle ID {vehicle_id} deleted by {request.user.username}")
        messages.success(request, "Vehicle deleted successfully!")  # Optional success message
        return redirect('vehicle_list')  # Redirect to the vehicle list page
    
    messages.error(request, "Invalid request method!")  # Optional error message
    return redirect('vehicle_list')  # Redirect even if the method is incorrect


#Edit function
@login_required
def view_vehicle(request, vehicle_id):
    user_groups = request.user.groups.values_list('name', flat=True)  # Check if the user is in HR group
    is_superuser = request.user.is_superuser

    """ View vehicle details (Permission Required: STORE.view_vehicle) """
    if not request.user.has_perm('STORE.view_vehicle'):
        logger.warning(f"Unauthorized vehicle view by {request.user.username} on ID {vehicle_id}")
        messages.error(request, "You do not have permission to view vehicle records.")
        return redirect('indexpage')
    
    logger.info(f"Vehicle ID {vehicle_id} viewed by {request.user.username}")
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    return render(request, 'store/view_vehicle.html', locals())



#excel download
@login_required
def vehicle_download_excel(request):
    if not request.user.has_perm('STORE.view_vehicle'):
        logger.warning(f"Unauthorized Excel download by {request.user.username}")
        messages.error(request, "You do not have permission to download vehicle records.")
        return redirect('indexpage')

    # Get filters
    filters = {
        'reporting_date': request.GET.get('reporting_date', ''),
        'name_of_supplier': request.GET.get('name_of_supplier', ''),
        'material': request.GET.get('material', ''),
        'name_of_transporter': request.GET.get('name_of_transporter', ''),
        'status': request.GET.get('status', ''),
    }

    vehicles = Vehicle.objects.all()

    for key, value in filters.items():
        if value:
            vehicles = vehicles.filter(**{f"{key}__icontains": value})

    # Create DataFrame
    data = vehicles.values(
        'reporting_date',
        'invoice',
        'name_of_supplier',
        'material',
        'unit',
        'qty',
        'report_time',
        'unloading_date',
        'unloading_time',
        'unloading_days',
        'vehicle_no',
        'name_of_transporter',
        'status',
        'manufacture',
        'remark',
    )

    try:
        df = pd.DataFrame(data)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=vehicle_records.xlsx'

        with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Vehicles', index=False)

        logger.info(f"{vehicles.count()} vehicle records exported to Excel by {request.user.username}")
        return response

    except Exception as e:
        logger.exception(f"Error generating Excel for vehicle records by {request.user.username}")
        messages.error(request, "An error occurred while generating the Excel file.")
        return redirect('vehicle_list')
    

def vehicle_chart_report(request):
    user_groups      = request.user.groups.values_list('name', flat=True)
    is_superuser     = request.user.is_superuser
    today            = date.today()
    year             = int(request.GET.get('year', today.year))
    month            = int(request.GET.get('month', today.month))
    period           = request.GET.get('period', 'monthly')
    material_filter  = request.GET.get('material', '')
    supplier_filter  = request.GET.get('supplier', '')

    # Base queryset
    qs = Vehicle.objects.filter(
        reporting_date__year=year,
        reporting_date__month=month
    )
    if material_filter:
        qs = qs.filter(material=material_filter)
    if supplier_filter:
        qs = qs.filter(name_of_supplier=supplier_filter)

    #
    # 1) Build the Material chart data
    #
    materials = list(
        qs.values_list('material', flat=True)
          .distinct()
          .order_by('material')
    )
    # get counts per material
    mat_counts = (
        qs.values('material')
          .annotate(count=Count('id'))
          .order_by('material')
    )
    mat_map = {row['material']: row['count'] for row in mat_counts}

    labels   = materials
    datasets = [{
        'label': f"Month {month:02d}/{year}",
        'data':  [mat_map.get(m, 0) for m in materials],
        'backgroundColor': 'rgba(54, 162, 235, 0.6)',
        'borderColor':     'rgba(54, 162, 235, 1)',
        'borderWidth': 1,
    }]

    #
    # 2) Build the Supplier chart data (bar-only)
    #
    suppliers = list(
        qs.values_list('name_of_supplier', flat=True)
          .distinct()
          .order_by('name_of_supplier')
    )

    if period == 'fortnightly':
        first_qs  = qs.filter(reporting_date__day__lte=15)
        second_qs = qs.filter(reporting_date__day__gte=16)

        first_counts  = (
            first_qs.values('name_of_supplier')
                    .annotate(count=Count('id'))
                    .order_by('name_of_supplier')
        )
        second_counts = (
            second_qs.values('name_of_supplier')
                     .annotate(count=Count('id'))
                     .order_by('name_of_supplier')
        )

        first_map  = {r['name_of_supplier']: r['count'] for r in first_counts}
        second_map = {r['name_of_supplier']: r['count'] for r in second_counts}

        supplier_labels   = suppliers
        supplier_datasets = [
            {
                'label': f"Days 1–15 ({month:02d}/{year})",
                'data':  [first_map.get(s, 0) for s in suppliers],
            },
            {
                'label': f"Days 16–{monthrange(year,month)[1]} ({month:02d}/{year})",
                'data':  [second_map.get(s, 0) for s in suppliers],
            },
        ]
    else:
        # monthly
        sup_counts = (
            qs.values('name_of_supplier')
              .annotate(count=Count('id'))
              .order_by('name_of_supplier')
        )
        sup_map = {r['name_of_supplier']: r['count'] for r in sup_counts}

        supplier_labels   = suppliers
        supplier_datasets = [
            {
                'label': f"Month {month:02d}/{year}",
                'data':  [sup_map.get(s, 0) for s in suppliers],
            }
        ]

    # --- dropdown choices ---
    month_choices    = [(m, date(2000, m, 1).strftime('%B')) for m in range(1, 13)]
    year_choices     = [today.year - 1, today.year, today.year + 1]
    material_choices = list(
        Vehicle.objects.filter(reporting_date__year=year,
                               reporting_date__month=month)
               .values_list('material', flat=True)
               .distinct().order_by('material')
    )
    supplier_choices = list(
        Vehicle.objects.filter(reporting_date__year=year,
                               reporting_date__month=month)
               .values_list('name_of_supplier', flat=True)
               .distinct().order_by('name_of_supplier')
    )

    return render(request, 'store/vehicle_chart_report.html', {
        # Material chart
        'labels':            labels,
        'datasets':          datasets,
        # Supplier chart
        'supplier_labels':   supplier_labels,
        'supplier_datasets': supplier_datasets,
        # Filters
        'year':              year,
        'month':             month,
        'period':            period,
        'material_choices':  material_choices,
        'selected_material': material_filter,
        'supplier_choices':  supplier_choices,
        'selected_supplier': supplier_filter,
        'month_choices':     month_choices,
        'year_choices':      year_choices,
        # auth
        'user_groups':       user_groups,
        'is_superuser':      is_superuser,
    })



@login_required
def material_list(request):
    """
    List all Dispatch Plan entries.
    """
    qs = MaterialRequest.objects.all().order_by('-created_at')
    logger.info(f"{request.user} viewed material list ({qs.count()} items)")
    return render(request, 'store/material_list.html', {
        'requests': qs,
    })


@login_required
def material_create(request):
    
    """
    Create a new Dispatch Plan.
    """
    if request.method == 'POST':
        form = MaterialRequestForm(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Dispatch Plan saved successfully.")
            logger.info(f"{request.user} created MaterialRequest #{obj.pk}")
            return redirect('material-list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = MaterialRequestForm()

    return render(request, 'store/material_form.html', {
        'form': form,
        'view': request,  # so template can do {% if view.object %} safely
    })


@login_required
def material_detail(request, pk):
    """
    Show a single Dispatch Plan.
    """
    obj = get_object_or_404(MaterialRequest, pk=pk)
    logger.info(f"{request.user} viewed MaterialRequest #{pk}")
    return render(request, 'store/material_detail.html', {
        'object': obj,
    })


@login_required
def material_edit(request, pk):
    """
    Edit an existing Dispatch Plan.
    """
    obj = get_object_or_404(MaterialRequest, pk=pk)

    if request.method == 'POST':
        form = MaterialRequestForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Dispatch Plan updated successfully.")
            logger.info(f"{request.user} updated MaterialRequest #{pk}")
            return redirect('material-list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = MaterialRequestForm(instance=obj)

    return render(request, 'store/material_form.html', {
        'form': form,
        'view': request,  # template uses view.object to know “edit” vs “new”
    })


@login_required
def material_delete(request, pk):
    """
    Confirm & delete a Dispatch Plan.
    GET  → show confirm page
    POST → delete and redirect
    """
    obj = get_object_or_404(MaterialRequest, pk=pk)

    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Dispatch Plan deleted.")
        logger.info(f"{request.user} deleted MaterialRequest #{pk}")
        return redirect('material-list')

    return render(request, 'store/material_confirm_delete.html', {
        'object': obj,
    })