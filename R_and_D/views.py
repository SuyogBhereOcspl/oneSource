from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import * 
from .forms import RAndDMoistureForm
from django.shortcuts import get_object_or_404
from django.db.models import Q
import io
import xlsxwriter
from django.http import HttpResponse
from .models import KFFactorEntry, KFFactorEntryLine
from .forms import KFFactorEntryForm, KFFactorEntryLineFormSet
from django.utils import timezone



@login_required
def add_r_and_d_moisture(request):
    user_groups      = request.user.groups.values_list('name', flat=True)
    is_superuser     = request.user.is_superuser
    show_admin_panel = is_superuser or (request.user.is_staff and request.user.is_active)

    if not request.user.has_perm('R_and_D.add_r_and_d_moisture'):
        messages.error(request, "You do not have permission to add R&D Moisture records.")
        return redirect('indexpage')

    if request.method == 'POST':
        form = RAndDMoistureForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Moisture record added successfully!")
            return redirect('r_and_d_moisture_list')  # Change to your actual list view name
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RAndDMoistureForm()

    return render(request, 'r_and_d/moisture_form.html', {
        'form': form,
        'active_link': 'r_and_d_moisture',
        'user_groups':       user_groups,
        'is_superuser':      is_superuser,
        'show_admin_panel':show_admin_panel,
        
    })


@login_required
def r_and_d_moisture_list(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser
    show_admin_panel = is_superuser or (request.user.is_staff and request.user.is_active)

    records = R_and_D_Moisture.objects.all()

    # FILTERS
    entry_date_from = request.GET.get('entry_date_from')
    entry_date_to = request.GET.get('entry_date_to')
    product_name = request.GET.get('product_name', '').strip()
    batch_no = request.GET.get('batch_no', '').strip()
    unit = request.GET.get('unit', '').strip()
    instrument = request.GET.get('instrument', '').strip()
    analysed_by = request.GET.get('analysed_by', '').strip()

    if entry_date_from:
        records = records.filter(entry_date__gte=entry_date_from)
    if entry_date_to:
        records = records.filter(entry_date__lte=entry_date_to)
    if product_name:
        records = records.filter(product_name__icontains=product_name)
    if batch_no:
        records = records.filter(batch_no__icontains=batch_no)
    if unit:
        records = records.filter(unit__name__icontains=unit)
    if instrument:
        records = records.filter(instrument__name__icontains=instrument)
    if analysed_by:
        records = records.filter(analysed_by__name__icontains=analysed_by)

    records = records.order_by('-entry_date', '-id')
    paginator = Paginator(records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'r_and_d/moisture_list.html', {
        'page_obj': page_obj,
        'active_link': 'r_and_d_moisture',
        'user_groups': user_groups,
        'is_superuser': is_superuser,
        'show_admin_panel':show_admin_panel,
        'filters': {
            'entry_date_from': entry_date_from or '',
            'entry_date_to': entry_date_to or '',
            'product_name': product_name,
            'batch_no': batch_no,
            'unit': unit,
            'instrument': instrument,
            'analysed_by': analysed_by,
        }
    })


@login_required
def edit_r_and_d_moisture(request, pk):
    user_groups      = request.user.groups.values_list('name', flat=True)
    is_superuser     = request.user.is_superuser
    show_admin_panel = is_superuser or (request.user.is_staff and request.user.is_active)
    obj = get_object_or_404(R_and_D_Moisture, pk=pk)
    if request.method == 'POST':
        form = RAndDMoistureForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Moisture record updated successfully!")
            return redirect('r_and_d_moisture_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RAndDMoistureForm(instance=obj)

    return render(request, 'r_and_d/moisture_form.html', {
        'form': form,
        'active_link': 'r_and_d_moisture',
        'user_groups':       user_groups,
        'is_superuser':      is_superuser,
        'show_admin_panel':show_admin_panel,
    })



@login_required
def delete_r_and_d_moisture(request, pk):
    obj = get_object_or_404(R_and_D_Moisture, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Moisture record deleted successfully!")
        return redirect('r_and_d_moisture_list')
    return redirect('r_and_d_moisture_list')



@login_required
def r_and_d_moisture_download_xlsx(request):
    import io
    import xlsxwriter
    from django.http import HttpResponse

    records = R_and_D_Moisture.objects.all()

    # Apply filters (same as your list view)
    entry_date_from = request.GET.get('entry_date_from')
    entry_date_to = request.GET.get('entry_date_to')
    product_name = request.GET.get('product_name', '').strip()
    batch_no = request.GET.get('batch_no', '').strip()
    unit = request.GET.get('unit', '').strip()
    instrument = request.GET.get('instrument', '').strip()
    analysed_by = request.GET.get('analysed_by', '').strip()

    if entry_date_from:
        records = records.filter(entry_date__gte=entry_date_from)
    if entry_date_to:
        records = records.filter(entry_date__lte=entry_date_to)
    if product_name:
        records = records.filter(product_name__icontains=product_name)
    if batch_no:
        records = records.filter(batch_no__icontains=batch_no)
    if unit:
        records = records.filter(unit__name__icontains=unit)
    if instrument:
        records = records.filter(instrument__name__icontains=instrument)
    if analysed_by:
        records = records.filter(analysed_by__name__icontains=analysed_by)

    records = records.order_by('-entry_date', '-id')

    # Create the in-memory file
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Moisture Records")

    # Define the header format
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4682B4',  # Deep blue
        'font_color': '#FFFFFF',
        'border': 1,
        'align': 'center'
    })

    # Headers including Sr. No
    headers = [
        "Sr. No",  # <--- Added Sr. No
        "Entry Date", "Entry Time", "ELN ID", "Product", "Batch No", "Sample Description", "Unit",
        "Instrument", "Factor (mg/mL)", "Sample Weight (gm)", "Burette Reading (mL)", "Moisture (%)",
        "Analysed By", "Completed Date", "Completed Time"
    ]

    # Write headers with format
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)

    # Write data rows with Sr. No as first column
    for row_num, obj in enumerate(records, 1):
        worksheet.write(row_num, 0, row_num)  # Sr. No
        worksheet.write(row_num, 1, obj.entry_date.strftime('%d-%m-%Y') if obj.entry_date else '')
        worksheet.write(row_num, 2, obj.entry_time.strftime('%H:%M') if obj.entry_time else '')
        worksheet.write(row_num, 3, obj.eln_id or '')
        worksheet.write(row_num, 4, obj.product_name if obj.product_name else '')
        worksheet.write(row_num, 5, obj.batch_no)
        worksheet.write(row_num, 6, obj.sample_description)
        worksheet.write(row_num, 7, obj.unit.name if obj.unit else '')
        worksheet.write(row_num, 8, obj.instrument.name if obj.instrument else '')
        worksheet.write(row_num, 9, float(obj.factor_mg_per_ml) if obj.factor_mg_per_ml else '')
        worksheet.write(row_num, 10, float(obj.sample_weight_gm) if obj.sample_weight_gm else '')
        worksheet.write(row_num, 11, float(obj.burette_reading_ml) if obj.burette_reading_ml else '')
        worksheet.write(row_num, 12, float(obj.moisture_percent) if obj.moisture_percent else '')
        worksheet.write(row_num, 13, obj.analysed_by.name if obj.analysed_by else '')
        worksheet.write(row_num, 14, obj.completed_date.strftime('%d-%m-%Y') if obj.completed_date else '')
        worksheet.write(row_num, 15, obj.completed_time.strftime('%H:%M') if obj.completed_time else '')

    workbook.close()
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=R_and_D_Moisture.xlsx'
    return response




@login_required
def add_kf_factor_entry(request):
    if request.method == 'POST':
        form = KFFactorEntryForm(request.POST)
        formset = KFFactorEntryLineFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            entry = form.save(commit=False)
            entry.date = timezone.now().date()  # Automatically set the date
            entry.save()
            formset.instance = entry
            formset.save()
            messages.success(request, "KF Factor Entry added successfully.")
            # return redirect('kf_factor_entry_list')  # Change to your list/detail url
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = KFFactorEntryForm()
        formset = KFFactorEntryLineFormSet()

    return render(request, 'r_and_d/add_kf_factor_entry.html', {
        'form': form,
        'formset': formset,
    })


def kf_factor_entry_list(request):
    entries = KFFactorEntry.objects.prefetch_related('lines', 'instrument', 'analysed_by').order_by('-created_at')
    table_data = []
    for entry in entries:
        lines = list(entry.lines.all())
        while len(lines) < 3:
            lines.append(None)
        kf_factors = [l.kf_factor for l in lines if l]
        avg_kf = round(sum(kf_factors) / len(kf_factors), 4) if kf_factors else ''
        table_data.append({
            'entry': entry,
            'lines': lines,
            'avg_kf': avg_kf,
        })
    return render(request, 'r_and_d/kf_factor_entry_list.html', {
        'table_data': table_data,
        'range3': range(3),    # <--- add this
    })