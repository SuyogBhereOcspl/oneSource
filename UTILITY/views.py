from itertools import groupby
from operator import attrgetter
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.forms import formset_factory
from django.contrib import messages
from django.db.models import Max
from django.http import Http404,HttpResponse
from decimal import Decimal
from .forms import UtilityRecordForm, TYPE_CHOICES
from .models import UtilityRecord
from django.shortcuts import render
from .models import UtilityRecord
import sys # Optional: For debugging print statements
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from datetime import datetime,date
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import xlsxwriter
from io import BytesIO
from django.utils import timezone
import io





#Add entry function






@login_required
def entry_view(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser

    if not request.user.has_perm('UTILITY.add_utilityrecord'):
        messages.error(request, "You do not have permission to Add Utility records.")
        return redirect('indexpage')

    UtilityFormSet = formset_factory(UtilityRecordForm, extra=0)

    if request.method == "POST":
        date = request.POST.get("date")
        formset = UtilityFormSet(request.POST)
        if formset.is_valid():
            # Remove any existing for that date
            UtilityRecord.objects.filter(reading_date=date).delete()
            for form in formset:
                rec = form.save(commit=False)
                rec.reading_date = date
                rec.save()
            messages.success(request, f"✅utility Readings saved!")
            return redirect("utility_readings_report")
    else:
        # One blank form per TYPE_CHOICES
        initial = [{"reading_type": t} for t, _ in TYPE_CHOICES]
        formset = UtilityFormSet(initial=initial)

    return render(request, "utility/utility_entry.html", {
        "formset": formset,
        'user_groups': user_groups,
        'is_superuser': is_superuser,
    })
    

#Edit function
@login_required
def edit_utility_date(request, date_str):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser

    if not request.user.has_perm('UTILITY.change_utilityrecord'):
        messages.error(request, "You do not have permission to update Utility records.")
        return redirect('indexpage')

    UtilityFormSet = formset_factory(UtilityRecordForm, extra=0)
    # Convert string to date object
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        messages.error(request, "Invalid date format.")
        return redirect("utility_readings_report")

    batch_qs = UtilityRecord.objects.filter(reading_date=date_obj).order_by('reading_type')
    if not batch_qs.exists():
        messages.error(request, "No records found for that date.")
        return redirect("utility_readings_report")

    if request.method == "POST":
        formset = UtilityFormSet(request.POST)
        if formset.is_valid():
            UtilityRecord.objects.filter(reading_date=date_obj).delete()
            for form in formset:
                rec = form.save(commit=False)
                rec.reading_date = date_obj
                rec.save()
            messages.success(request, f"✅ Readings updated for {date_obj}!")
            return redirect("utility_readings_report")
    else:
        type_map = {rec.reading_type: rec for rec in batch_qs}
        initial = []
        for t, _ in TYPE_CHOICES:
            rec = type_map.get(t)
            if rec:
                data = {"reading_type": rec.reading_type}
                for fld in UtilityRecord._meta.fields:
                    name = fld.name
                    if name not in ("id", "reading_date", "reading_type"):
                        data[name] = getattr(rec, name)
                initial.append(data)
            else:
                initial.append({"reading_type": t})
        formset = UtilityFormSet(initial=initial)

    return render(request, "utility/utility_entry.html", {
        "formset": formset,
        "edit_date": date_obj,  # Pass the date object, not string
        'user_groups': user_groups,
        'is_superuser': is_superuser,
    })





#Delete reading date
@login_required
def delete_utility_date(request, date_str):
    user_groups = request.user.groups.values_list('name', flat=True)  # Check if the user is in HR group
    is_superuser = request.user.is_superuser

    """ View UTILITY details (Permission Required: UTILITY.delete_utilityrecord) """
    if not request.user.has_perm('UTILITY.delete_utilityrecord'):
        messages.error(request, "You do not have permission to Delete Utility records.")
        return redirect('indexpage')
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        messages.error(request, "Invalid date format.")
        return redirect("utility_readings_report")

    records = UtilityRecord.objects.filter(reading_date=date_obj)
    if not records.exists():
        messages.error(request, "No records found for the selected date.")
        return redirect('utility_readings_report')

    if request.method == "POST":
        count, _ = records.delete()
    messages.success(request, f"Deleted record(s) for {date_str}.")
    return redirect('utility_readings_report')

   

# -----------------------------------------------------------------------------------------------------

ACTUAL_TYPE_FIELDS_OWNERSHIP = {
    "STEAM GENERATION READING": ["sb_3_e_22_main_fm_fv", "sb_3_sub_fm_oc"],
    "STEAM CONSUMPTION READING": [
        "block_a_reading", "block_b_reading", "mee_total_reading", "stripper_reading",
        "old_atfd", "mps_d_block_reading", "lps_e_17", "mps_e_17",
        "jet_ejector_atfd_c", "deareator", "new_atfd"
    ],
    "Boiler Water meter Reading": ["boiler_water_meter"],
    "MIDC reading": ["midc_water_e_18", "midc_water_e_17", "midc_water_e_22", "midc_water_e_16", "midc_water_e_20"],
    "BRIQUETTE": ["briquette_sb_3"],
    "DM Water consumed for boiler": ["dm_water_for_boiler"], # Not in Excel, but in model
}


DISPLAY_HEADER_STRUCTURE = [
    {
        'group_label': 'STEAM GENERATION READING',
        'fields': [
            ('sb_3_e_22_main_fm_fv', 'SB-3 (E-22)<br>(Main FM FV)'),
            ('sb_3_sub_fm_oc', 'SB-3 (Sub FM OC)'),
        ],
        'group_bg_color': 'bg-green-200',
        'cell_bg_color': 'bg-green-50'
    },
    {
        'group_label': 'STEAM CONSUMPTION READING',
        'fields': [
            ('block_a_reading', 'Block-A<br>Reading'),
            ('block_b_reading', 'Block_B<br>Reading'),
            ('mee_total_reading', 'MEE<br>Total<br>Reading'),
            ('stripper_reading', 'Stripper<br>Reading'),
            ('old_atfd', 'Old ATFD'),
            ('mps_d_block_reading', 'MPS D-<br>block<br>reading'),
            ('lps_e_17', 'LPS E-17'),
            ('mps_e_17', 'MPS E-17'),
            ('new_atfd', 'New ATFD'),
        ],
        'group_bg_color': 'bg-blue-200',
        'cell_bg_color': 'bg-blue-50'
    },
    { # Grouping Boiler Water alone or with other general water readings
        'group_label': ' ', # Empty group label as it's a single main column in Excel
        'fields': [
            ('boiler_water_meter', 'Boiler<br>Water<br>meter<br>Reading'),
        ],
        'group_bg_color': 'bg-purple-200', # No group header in excel, so cell color dominates
        'cell_bg_color': 'bg-purple-50'
    },
    {
        'group_label': 'MIDC reading',
        'fields': [
            ('midc_water_e_18', 'MIDC<br>Water<br>Reading<br>E-18'),
            ('midc_water_e_17', 'MIDC<br>Water<br>Reading<br>E-17'),
            ('midc_water_e_22', 'MIDC<br>Water<br>Reading<br>E-22'),
            ('midc_water_e_16', 'MIDC<br>Water<br>Reading<br>E-16'),
            ('midc_water_e_20', 'MIDC<br>Water<br>Reading<br>E-20'), # In model, not Excel. Uncomment to display.
        ],
        'group_bg_color': 'bg-sky-200',
        'cell_bg_color': 'bg-sky-50'
    },
]

# This flat list determines the order of data cells in each row.
ORDERED_DISPLAY_FIELDS = []
for group in DISPLAY_HEADER_STRUCTURE:
    for field_name, _ in group['fields']:
        ORDERED_DISPLAY_FIELDS.append(field_name)


@login_required
def utility_readings_report(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser

    if not request.user.has_perm('UTILITY.view_utilityrecord'):
        messages.error(request, "You do not have permission to View Utility records.")
        return redirect('indexpage')

    # ----- Add date filters -----
    from_date = request.GET.get('from_date')
    to_date   = request.GET.get('to_date')
    date_filter = {}

    if from_date:
        date_filter['reading_date__gte'] = from_date
    if to_date:
        date_filter['reading_date__lte'] = to_date

    # Filter distinct_dates based on selected period
    distinct_dates = UtilityRecord.objects.filter(**date_filter) \
                        .values_list('reading_date', flat=True) \
                        .distinct().order_by('-reading_date')

    # ------------- PAGINATION -------------
    page_number = request.GET.get('page', 1)
    per_page = 10  # Change this value as needed
    paginator = Paginator(distinct_dates, per_page)
    page_obj = paginator.get_page(page_number)
    paged_dates = page_obj.object_list
    # --------------------------------------

    report_data_rows = []

    all_records_for_dates = UtilityRecord.objects.filter(reading_date__in=list(paged_dates)) \
                                                .order_by('reading_date', 'reading_type', 'id')

    records_by_date_then_type = defaultdict(dict)
    for record in all_records_for_dates:
        records_by_date_then_type[record.reading_date][record.reading_type] = record

    for r_date in paged_dates:
        consolidated_readings_for_date = {field_name: None for field_name in ORDERED_DISPLAY_FIELDS}
        records_for_type_on_this_date = records_by_date_then_type.get(r_date, {})
        for reading_type_key, owned_fields in ACTUAL_TYPE_FIELDS_OWNERSHIP.items():
            record_for_type = records_for_type_on_this_date.get(reading_type_key)
            if record_for_type:
                for model_field in owned_fields:
                    if model_field in consolidated_readings_for_date:
                        consolidated_readings_for_date[model_field] = getattr(record_for_type, model_field, None)
        ordered_values_for_row = []
        for field_name in ORDERED_DISPLAY_FIELDS:
            raw_value = consolidated_readings_for_date.get(field_name)
            processed_value = None
            if isinstance(raw_value, Decimal):
                processed_value = raw_value
            elif raw_value is not None:
                try:
                    processed_value = Decimal(str(raw_value))
                except InvalidOperation:
                    processed_value = None
            ordered_values_for_row.append({
                'name': field_name,
                'value': processed_value
            })
        report_data_rows.append({
            'date': r_date,
            'values': ordered_values_for_row
        })

    context = {
        'header_structure': DISPLAY_HEADER_STRUCTURE,
        'report_rows': report_data_rows,
        'user_groups': user_groups,
        'is_superuser': is_superuser,
        'from_date': from_date or '',
        'to_date': to_date or '',
        'page_obj': page_obj,  # Pass to template
    }
    return render(request, 'utility/utility_readings_report.html', context)




#-----------Excel Download  ----------------------------
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.timezone import now # For default dates if needed, though your code handles it
from collections import defaultdict
from io import BytesIO
import xlsxwriter
from decimal import Decimal

# Assuming UtilityRecord, DISPLAY_HEADER_STRUCTURE, ORDERED_DISPLAY_FIELDS,
# and ACTUAL_TYPE_FIELDS_OWNERSHIP are defined elsewhere and imported correctly.
# from .models import UtilityRecord
# from .your_constants_module import DISPLAY_HEADER_STRUCTURE, ORDERED_DISPLAY_FIELDS, ACTUAL_TYPE_FIELDS_OWNERSHIP

@login_required
def utility_readings_excel(request):
    if not request.user.has_perm('UTILITY.view_utilityrecord'):
        return HttpResponse("Unauthorized", status=403)

    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')
    # The 'page' parameter is no longer needed for Excel export logic
    # page = request.GET.get('page', 1)

    date_filter = {}
    if from_date_str:
        date_filter['reading_date__gte'] = from_date_str
    if to_date_str:
        date_filter['reading_date__lte'] = to_date_str

    # Get ALL distinct dates within the filter range for the Excel report
    # No pagination here.
    report_dates = UtilityRecord.objects.filter(**date_filter) \
        .values_list('reading_date', flat=True).distinct().order_by('-reading_date')

    # If there are no dates, we can return an empty Excel or a message.
    # For now, it will proceed and create an Excel with only headers.
    if not report_dates:
        # Optionally, handle the case of no data differently, e.g.,
        # return HttpResponse("No data found for the selected date range.", status=200)
        pass # Or let it generate an empty report

    # Fetch all records for ALL the distinct dates found
    all_records_for_report_dates = UtilityRecord.objects.filter(reading_date__in=list(report_dates)) \
        .order_by('reading_date', 'reading_type', 'id')

    records_by_date_then_type = defaultdict(dict)
    for record in all_records_for_report_dates:
        records_by_date_then_type[record.reading_date][record.reading_type] = record

    # --- Prepare Excel file in memory ---
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Utility Readings')

    # Styles
    bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
    center = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
    border = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
    group_header_fmt = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#dbeafe', 'border': 1, 'valign': 'vcenter'})
    sub_header_fmt = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#f1f5f9', 'border': 1, 'valign': 'vcenter'})

    # -- Header row 1: Group labels (merged cells) --
    current_col_header1 = 0
    worksheet.merge_range(0, 0, 1, 0, "DATE", group_header_fmt)  # Date header
    current_col_header1 = 1 # Start after DATE column
    for group in DISPLAY_HEADER_STRUCTURE:
        group_span = len(group['fields'])
        if group_span == 1:
            worksheet.write(0, current_col_header1, group['group_label'], group_header_fmt)
            current_col_header1 += 1
        elif group_span > 1: # Ensure span is positive
            worksheet.merge_range(0, current_col_header1, 0, current_col_header1 + group_span - 1, group['group_label'], group_header_fmt)
            current_col_header1 += group_span
        # If group_span is 0 or less, it might indicate an issue with DISPLAY_HEADER_STRUCTURE

    # -- Header row 2: Field labels --
    current_col_header2 = 1 # Start after DATE column
    for group in DISPLAY_HEADER_STRUCTURE:
        for field_name, label in group['fields']:
            clean_label = label.replace('<br>', ' ').replace(' ', ' ').strip()
            worksheet.write(1, current_col_header2, clean_label, sub_header_fmt)
            current_col_header2 += 1

    # --- Data rows ---
    # Iterate over all 'report_dates' instead of 'paged_dates'
    for row_idx, r_date in enumerate(report_dates, start=2): # Start at row 2 (0-indexed) for data
        worksheet.write(row_idx, 0, r_date.strftime("%d/%m/%Y"), border) # Date in first column

        consolidated_readings_for_date = {field_name: None for field_name in ORDERED_DISPLAY_FIELDS}
        records_for_type_on_this_date = records_by_date_then_type.get(r_date, {})

        for reading_type_key, owned_fields in ACTUAL_TYPE_FIELDS_OWNERSHIP.items():
            record_for_type = records_for_type_on_this_date.get(reading_type_key)
            if record_for_type:
                for model_field in owned_fields:
                    if model_field in consolidated_readings_for_date: # Check if field is expected in output
                        consolidated_readings_for_date[model_field] = getattr(record_for_type, model_field, None)

        # Write all values for this date according to ORDERED_DISPLAY_FIELDS
        for col_idx_offset, field_name in enumerate(ORDERED_DISPLAY_FIELDS):
            actual_col_idx = col_idx_offset + 1 # Data columns start after the DATE column
            val = consolidated_readings_for_date.get(field_name)
            try:
                if isinstance(val, Decimal):
                    # xlsxwriter prefers float for numbers
                    worksheet.write_number(row_idx, actual_col_idx, float(val), border)
                elif isinstance(val, (int, float)): # Handle existing floats/ints
                    worksheet.write_number(row_idx, actual_col_idx, float(val), border)
                elif val is not None:
                    # Attempt to convert to float if it looks like a number, otherwise write as string
                    try:
                        num_val = float(val)
                        worksheet.write_number(row_idx, actual_col_idx, num_val, border)
                    except (ValueError, TypeError):
                        worksheet.write_string(row_idx, actual_col_idx, str(val), border)
                else: # val is None
                    worksheet.write_blank(row_idx, actual_col_idx, None, border) # Explicitly write blank
            except Exception: # Catch-all for any other conversion errors
                worksheet.write_string(row_idx, actual_col_idx, str(val) if val is not None else '', border)


    # Set column width for better visibility
    worksheet.set_column(0, 0, 12) # Date column width
    if ORDERED_DISPLAY_FIELDS: # Check if there are other fields
        worksheet.set_column(1, len(ORDERED_DISPLAY_FIELDS), 15) # Default width for data columns

    workbook.close()
    output.seek(0)

    filename = f"Utility_Readings_{now().strftime('%Y%m%d')}.xlsx" # Add date to filename
    response = HttpResponse(
        output,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"' # Ensure filename is quoted
    return response





#---------------------------------------------------------------------------------------------



# TYPE_FIELDS: Maps reading_type to model fields it contains.
TYPE_FIELDS = {
    "STEAM GENERATION READING": ["sb_3_e_22_main_fm_fv", "sb_3_sub_fm_oc"],
    "STEAM CONSUMPTION READING": [
        "block_a_reading", "block_b_reading", "mee_total_reading", "stripper_reading",
        "old_atfd", "mps_d_block_reading", "lps_e_17", "mps_e_17",
        "jet_ejector_atfd_c", "deareator", "new_atfd"
    ],
    "Boiler Water meter Reading": ["boiler_water_meter"],
    "MIDC reading": ["midc_water_e_17", "midc_water_e_16", "midc_water_e_22", "midc_water_e_18", "midc_water_e_20"],
    "BRIQUETTE": ["briquette_sb_3"],
    "DM Water consumed for boiler": ["dm_water_for_boiler"],
}

HEADER_STRUCTURE = [
    {
        'group_label': 'STEAM GENERATION',
        'fields': [
            ('sb_3_e_22_main_fm_fv', 'SB-3 (E-22) Main FM/FV', 'bg-orange-50'),
            ('sb_3_sub_fm_oc', 'SB-3 Sub FM/OC', 'bg-green-50'),
        ]
    },
    {
        'group_label': 'STEAM CONSUMPTION',
        'fields': [
            ('block_a_reading', 'Block-A', 'bg-blue-100'),
            ('block_b_reading', 'Block-B', 'bg-blue-100'),
            ('mee_total_reading', 'MEE', 'bg-blue-100'),
            ('stripper_reading', 'Stripper', 'bg-blue-100'),
            ('old_atfd', 'Old ATFD', 'bg-blue-100'),
            ('mps_d_block_reading', 'D-Block MPS', 'bg-blue-100'),
            ('lps_e_17', 'LPS E-17', 'bg-blue-100'),
            ('mps_e_17', 'MPS E-17', 'bg-blue-100'),
            ('jet_ejector_atfd_c', '4 JET Ejector + ATFD-C', 'bg-blue-100'),
            ('deareator', 'Deareator', 'bg-blue-100'),
            ('new_atfd', 'New ATFD', 'bg-blue-100'),
        ]
    },
    {
        'group_label': 'BRIQUETTE',
        'fields': [
            ('briquette_sb_3', 'SB-3', 'bg-yellow-50'),
        ]
    },
    {
        'group_label': 'Boiler Water meter Consumption',
        'fields': [
            ('boiler_water_meter', 'Boiler Water meter', 'bg-violet-100'),
        ]
    },
    {
        'group_label': 'DM Water consumption for boiler',
        'fields': [
            ('dm_water_for_boiler', 'DM Water consumed for boiler', 'bg-sky-100'),
        ]
    },
    {
        'group_label': 'WATER',
        'fields': [
            ('midc_water_e_17', 'MIDC water E-17', 'bg-sky-100'),
            ('midc_water_e_16', 'MIDC water E-16', 'bg-sky-100'),
            ('midc_water_e_22', 'MIDC water E-22', 'bg-sky-100'),
            ('midc_water_e_18', 'MIDC water E-18', 'bg-sky-100'),
            ('midc_water_e_20', 'MIDC water E-20', 'bg-sky-100'),
        ]
    }
]

# Defines which unique fields need their consumption calculated
UNIQUE_MODEL_FIELDS_FOR_CALCULATION = []
_seen_for_calc = set()
for group in HEADER_STRUCTURE:
    for field_name, _, _ in group['fields']:
        if field_name not in _seen_for_calc:
            UNIQUE_MODEL_FIELDS_FOR_CALCULATION.append(field_name)
            _seen_for_calc.add(field_name)

# Defines the order and repetition of fields as they appear in the report columns
ALL_DISPLAY_FIELDS_IN_ORDER = []
for group in HEADER_STRUCTURE:
    for field_name, _, _ in group['fields']:
        ALL_DISPLAY_FIELDS_IN_ORDER.append(field_name)


def get_today_value(records_for_types, field_name):
    for r_type, flds_in_type in TYPE_FIELDS.items():
        if field_name in flds_in_type:
            today_record = records_for_types.get(r_type)
            if today_record:
                val = getattr(today_record, field_name, None)
                if val is None:
                    return Decimal('0.00')
                if not isinstance(val, Decimal):
                    return Decimal(str(val))
                return val
    return Decimal('0.00')

@login_required
def utility_consumption_report(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser

    if not request.user.has_perm('UTILITY.view_utilityrecord'):
        messages.error(request, "You do not have permission to View Utility records.")
        return redirect('indexpage')

    from_date_str = request.GET.get("from_date", "")
    to_date_str = request.GET.get("to_date", "")

    if from_date_str and to_date_str:
        try:
            from_date = date.fromisoformat(from_date_str)
            to_date = date.fromisoformat(to_date_str)
        except Exception:
            from_date = None
            to_date = None
    else:
        from_date = None
        to_date = None

    qs = UtilityRecord.objects.all()
    if from_date and to_date:
        qs = qs.filter(reading_date__range=[from_date, to_date])

    all_distinct_dates = list(
        qs.values_list("reading_date", flat=True)
          .distinct()
          .order_by("-reading_date")
    )

    if len(all_distinct_dates) < 2:
        return render(request, "utility/utility_consumption_report.html", {
            "header_structure": HEADER_STRUCTURE,
            "report_rows": [],
            "from_date": from_date or "",
            "to_date": to_date or "",
            "error": "Need at least two days of readings to compute consumption.",
        })

    report_rows_data = []
    records_by_date_and_type = {}
    relevant_dates = set(all_distinct_dates)
    all_db_records = UtilityRecord.objects.filter(reading_date__in=relevant_dates).order_by('reading_date', 'reading_type', 'id')

    for record in all_db_records:
        date_key = record.reading_date
        type_key = record.reading_type
        if date_key not in records_by_date_and_type:
            records_by_date_and_type[date_key] = {}
        records_by_date_and_type[date_key][type_key] = record

    SHOW_AS_IS_FIELDS = ["briquette_sb_3", "deareator", "jet_ejector_atfd_c","dm_water_for_boiler"]

    for i in range(len(all_distinct_dates) - 1):
        today_date = all_distinct_dates[i]
        yesterday_date = all_distinct_dates[i + 1]

        today_records_for_all_types = records_by_date_and_type.get(today_date, {})
        yesterday_records_for_all_types = records_by_date_and_type.get(yesterday_date, {})

        calculated_deltas_map = {}
        total_steam_consumption_for_day = Decimal('0.00')

        for model_field_name in UNIQUE_MODEL_FIELDS_FOR_CALCULATION:
            delta = Decimal('0.00')
            field_reading_type = None
            for r_type, flds_in_type in TYPE_FIELDS.items():
                if model_field_name in flds_in_type:
                    field_reading_type = r_type
                    break

            if field_reading_type:
                today_record_for_type = today_records_for_all_types.get(field_reading_type)
                yesterday_record_for_type = yesterday_records_for_all_types.get(field_reading_type)

                if today_record_for_type and yesterday_record_for_type:
                    today_val_raw = getattr(today_record_for_type, model_field_name, None)
                    yesterday_val_raw = getattr(yesterday_record_for_type, model_field_name, None)

                    if today_val_raw is None: today_val = Decimal('0.00')
                    elif not isinstance(today_val_raw, Decimal): today_val = Decimal(str(today_val_raw))
                    else: today_val = today_val_raw

                    if yesterday_val_raw is None: yesterday_val = Decimal('0.00')
                    elif not isinstance(yesterday_val_raw, Decimal): yesterday_val = Decimal(str(yesterday_val_raw))
                    else: yesterday_val = yesterday_val_raw

                    delta = today_val - yesterday_val

                if model_field_name == 'mps_e_17':
                    delta = delta * Decimal('1000')

            calculated_deltas_map[model_field_name] = delta

            if field_reading_type == "STEAM CONSUMPTION READING":
                total_steam_consumption_for_day += delta

        mee = (
            calculated_deltas_map.get('mee_total_reading', Decimal('0.00')) +
            calculated_deltas_map.get('stripper_reading', Decimal('0.00')) +
            calculated_deltas_map.get('old_atfd', Decimal('0.00')) +
            calculated_deltas_map.get('new_atfd', Decimal('0.00'))
        )
        plant = (
            calculated_deltas_map.get('block_a_reading', Decimal('0.00')) +
            calculated_deltas_map.get('block_b_reading', Decimal('0.00')) +
            calculated_deltas_map.get('mps_d_block_reading', Decimal('0.00')) +
            calculated_deltas_map.get('lps_e_17', Decimal('0.00')) +
            calculated_deltas_map.get('mps_e_17', Decimal('0.00')) +
            get_today_value(today_records_for_all_types, 'jet_ejector_atfd_c') +
            get_today_value(today_records_for_all_types, 'deareator')
        )
        total = mee + plant

        current_day_display_values_list = []
        for display_field_name in ALL_DISPLAY_FIELDS_IN_ORDER:
            if display_field_name in SHOW_AS_IS_FIELDS:
                today_value = None
                for r_type, flds_in_type in TYPE_FIELDS.items():
                    if display_field_name in flds_in_type:
                        today_record = today_records_for_all_types.get(r_type)
                        if today_record:
                            today_value = getattr(today_record, display_field_name, None)
                        break
                if today_value is None:
                    value_to_display = Decimal('0.00')
                else:
                    value_to_display = today_value
            else:
                value_to_display = calculated_deltas_map.get(display_field_name, Decimal('0.00'))
            current_day_display_values_list.append(value_to_display)

        report_rows_data.append({
            'date': today_date,
            'values': current_day_display_values_list,
            'steam_calc': {
                'mee': mee,
                'plant': plant,
                'total': total,
            }
        })

    # PAGINATION
    per_page = 10  # Set your page size here
    paginator = Paginator(report_rows_data, per_page)
    page_number = request.GET.get("page") or 1

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        "title": "Daily Consumption Report",
        "header_structure": HEADER_STRUCTURE,
        "report_rows": page_obj.object_list,
        "from_date": from_date or "",
        "to_date": to_date or "",
        "error": None,
        "page_obj": page_obj,
        'user_groups': user_groups,
        'is_superuser': is_superuser,
    }
    return render(request, "utility/utility_consumption_report.html", context)






@login_required
def utility_consumption_excel(request):
    # Match new filter logic: show all dates if no filter is applied
    from_date_str = request.GET.get("from_date", "")
    to_date_str = request.GET.get("to_date", "")

    if from_date_str and to_date_str:
        try:
            from_date = date.fromisoformat(from_date_str)
            to_date = date.fromisoformat(to_date_str)
        except Exception:
            from_date = None
            to_date = None
    else:
        from_date = None
        to_date = None

    qs = UtilityRecord.objects.all()
    if from_date and to_date:
        qs = qs.filter(reading_date__range=[from_date, to_date])

    all_distinct_dates = list(
        qs.values_list("reading_date", flat=True)
          .distinct()
          .order_by("-reading_date")
    )

    records_by_date_and_type = {}
    relevant_dates = set(all_distinct_dates)
    all_db_records = UtilityRecord.objects.filter(reading_date__in=relevant_dates).order_by('reading_date', 'reading_type', 'id')

    for record in all_db_records:
        date_key = record.reading_date
        type_key = record.reading_type
        if date_key not in records_by_date_and_type:
            records_by_date_and_type[date_key] = {}
        records_by_date_and_type[date_key][type_key] = record

    SHOW_AS_IS_FIELDS = ["briquette_sb_3", "deareator", "jet_ejector_atfd_c","dm_water_for_boiler"]

    # Prepare Excel workbook in-memory
    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {'in_memory': True})
    ws = wb.add_worksheet('Utility Consumption')

    # Styles
    header_fmt = wb.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#e0edfa', 'border': 1})
    group_fmt  = wb.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#d1fae5', 'border': 1})
    th_fmt     = wb.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1})
    date_fmt   = wb.add_format({'num_format': 'dd/mm/yyyy', 'border': 1, 'align': 'center'})
    val_fmt    = wb.add_format({'num_format': '#,##0.00', 'border': 1, 'align': 'right'})
    val_bold   = wb.add_format({'num_format': '#,##0.00', 'border': 1, 'align': 'right', 'bold': True})
    
    # ---- Write Headers ----

    # 1st header row: group labels
    row, col = 0, 0
    ws.write(row, col, "DATE", group_fmt)
    col += 1
    for group in HEADER_STRUCTURE:
        ws.merge_range(row, col, row, col+len(group['fields'])-1, group['group_label'], group_fmt)
        col += len(group['fields'])
    ws.merge_range(row, col, row, col+2, "STEAM", group_fmt)

    # 2nd header row: field labels
    row, col = 1, 0
    ws.write(row, col, "", th_fmt)
    col += 1
    for group in HEADER_STRUCTURE:
        for _, label, _ in group['fields']:
            ws.write(row, col, label, th_fmt)
            col += 1
    ws.write(row, col, "MEE", th_fmt); col += 1
    ws.write(row, col, "PLANT", th_fmt); col += 1
    ws.write(row, col, "TOTAL", th_fmt)

    # ---- Write Data Rows ----

    for i in range(len(all_distinct_dates) - 1):
        today_date = all_distinct_dates[i]
        yesterday_date = all_distinct_dates[i + 1]
        today_records_for_all_types = records_by_date_and_type.get(today_date, {})
        yesterday_records_for_all_types = records_by_date_and_type.get(yesterday_date, {})

        calculated_deltas_map = {}
        for model_field_name in UNIQUE_MODEL_FIELDS_FOR_CALCULATION:
            delta = Decimal('0.00')
            field_reading_type = None
            for r_type, flds_in_type in TYPE_FIELDS.items():
                if model_field_name in flds_in_type:
                    field_reading_type = r_type
                    break

            if field_reading_type:
                today_record_for_type = today_records_for_all_types.get(field_reading_type)
                yesterday_record_for_type = yesterday_records_for_all_types.get(field_reading_type)

                if today_record_for_type and yesterday_record_for_type:
                    today_val_raw = getattr(today_record_for_type, model_field_name, None)
                    yesterday_val_raw = getattr(yesterday_record_for_type, model_field_name, None)
                    if today_val_raw is None: today_val = Decimal('0.00')
                    elif not isinstance(today_val_raw, Decimal): today_val = Decimal(str(today_val_raw))
                    else: today_val = today_val_raw
                    if yesterday_val_raw is None: yesterday_val = Decimal('0.00')
                    elif not isinstance(yesterday_val_raw, Decimal): yesterday_val = Decimal(str(yesterday_val_raw))
                    else: yesterday_val = yesterday_val_raw
                    delta = today_val - yesterday_val

                if model_field_name == 'mps_e_17':
                    delta = delta * Decimal('1000')

            calculated_deltas_map[model_field_name] = delta

        mee = (
            calculated_deltas_map.get('mee_total_reading', Decimal('0.00')) +
            calculated_deltas_map.get('stripper_reading', Decimal('0.00')) +
            calculated_deltas_map.get('old_atfd', Decimal('0.00')) +
            calculated_deltas_map.get('new_atfd', Decimal('0.00'))
        )
        plant = (
            calculated_deltas_map.get('block_a_reading', Decimal('0.00')) +
            calculated_deltas_map.get('block_b_reading', Decimal('0.00')) +
            calculated_deltas_map.get('mps_d_block_reading', Decimal('0.00')) +
            calculated_deltas_map.get('lps_e_17', Decimal('0.00')) +
            calculated_deltas_map.get('mps_e_17', Decimal('0.00')) +
            get_today_value(today_records_for_all_types, 'jet_ejector_atfd_c') +
            get_today_value(today_records_for_all_types, 'deareator')
        )
        total = mee + plant

        current_day_display_values_list = []
        for display_field_name in ALL_DISPLAY_FIELDS_IN_ORDER:
            if display_field_name in SHOW_AS_IS_FIELDS:
                today_value = None
                for r_type, flds_in_type in TYPE_FIELDS.items():
                    if display_field_name in flds_in_type:
                        today_record = today_records_for_all_types.get(r_type)
                        if today_record:
                            today_value = getattr(today_record, display_field_name, None)
                        break
                if today_value is None:
                    value_to_display = Decimal('0.00')
                else:
                    value_to_display = today_value
            else:
                value_to_display = calculated_deltas_map.get(display_field_name, Decimal('0.00'))
            current_day_display_values_list.append(value_to_display)

        row += 1
        col = 0
        ws.write(row, col, today_date, date_fmt)
        col += 1
        for v in current_day_display_values_list:
            ws.write(row, col, float(v), val_fmt)
            col += 1
        ws.write(row, col, float(mee), val_bold); col += 1
        ws.write(row, col, float(plant), val_bold); col += 1
        ws.write(row, col, float(total), val_bold)

    ws.autofilter(0, 0, row, col)  # Apply filter for user
    ws.freeze_panes(2, 1)          # Freeze headers

    wb.close()
    output.seek(0)

    # Handle filename for all/filtered cases
    if from_date_str and to_date_str:
        filename = f"Utility_Consumption_{from_date_str}_to_{to_date_str}.xlsx"
    else:
        filename = f"Utility_Consumption_All.xlsx"

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
