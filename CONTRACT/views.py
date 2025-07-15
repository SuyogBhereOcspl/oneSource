from django.shortcuts import render, redirect
from datetime import date,datetime
from .models import CONTRACT_NAME_CHOICES,SHIFT_CHOICES,ContractorManpowerAttendance,DepartmentManpowerRequirement
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from calendar import monthrange
from django.contrib import messages
import xlsxwriter
import io
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required




def contract_daily_attendance_entry(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser

    contractors = [c[0] for c in CONTRACT_NAME_CHOICES]
    contractor_choices = CONTRACT_NAME_CHOICES
    shifts = [s[0] for s in SHIFT_CHOICES]
    shift_choices = SHIFT_CHOICES

    departments = [
        ("A Block", "a_block"),
        ("B Block", "b_block"),
        ("C Block", "c_block"),
        ("D Block", "d_block"),
        ("PKG", "pkg"),
        ("Pilot", "pilot"),
        ("E Block- 17 Production", "e_block_17_production"),
        ("MEE/ETP", "mee_etp"),
        ("RO Plant", "ro_plant"),
        ("MNTS", "mnts"),
        ("ELE", "ele"),
        ("INST", "inst"),
        ("RM/ENGG 16 - 17 & 18", "rm_engg_16_17_18"),
        ("QC & PD", "qc_pd"),
        ("Boiler", "boiler"),
        ("Dozer Driver", "dozer_driver"),
        ("HouseKeeping 16 - 17 & 18", "housekeeping_16_17_18"),
        ("Office Boy", "office_boy"),
        ("Gardenar", "gardenar"),
        ("OHC", "ohc"),
        ("Painting", "painting"),
        ("MNTS-E 17", "mnts_e17"),
        ("ELE- E-17", "ele_e17"),
        ("INST-E-17", "inst_e17"),
    ]

    # --- Determine which date to edit ---
    today = request.GET.get('date') or request.POST.get('date') or date.today()
    if isinstance(today, str):
        today = date.fromisoformat(today)

    # On POST: Save/Update data
    if request.method == "POST":
        # Removed ContractorDailyRequirement saving block

        # Save ContractorManpowerAttendance (contractor/shift actuals)
        for contractor in contractors:
            for shift in shifts:
                save_kwargs = {
                    'date': today,
                    'contractor': contractor,
                    'shift': shift,
                }
                for dept_display, field_name in departments:
                    value = request.POST.get(f'{contractor}_{shift}_{field_name}', 0) or 0
                    save_kwargs[field_name] = value
                ContractorManpowerAttendance.objects.update_or_create(
                    date=today,
                    contractor=contractor,
                    shift=shift,
                    defaults=save_kwargs
                )
        # Add success message here
        messages.success(request, "Contractor manpower attendance saved successfully.")        
        return redirect("contract_daily_attendance_entry")  # Use your URL name

    # --- For GET: Prepare nested context with prefill values ---

    # Removed required_totals fetching

    # 2. Prefill all actuals per shift/contractor/department
    att_map = {}  # (contractor, shift) -> att instance
    for att in ContractorManpowerAttendance.objects.filter(date=today):
        att_map[(att.contractor, att.shift)] = att

    contractor_context = []
    for contractor, contractor_label in contractor_choices:
        shifts_context = []
        for shift, shift_label in shift_choices:
            dept_values = {}
            att = att_map.get((contractor, shift))
            for dept_display, field_name in departments:
                dept_values[dept_display] = getattr(att, field_name) if att else ''
            shifts_context.append({
                'shift': shift,
                'shift_label': shift_label,
                'dept_values': dept_values,
            })
        contractor_context.append({
            'contractor': contractor,
            'contractor_label': contractor_label,
            # removed 'required_total' key here as well
            'shifts': shifts_context,
        })

    return render(request, "contract/contractor_daily_entry.html", {
        'user_groups': user_groups,
        'is_superuser': is_superuser,
        "departments": departments,
        "contractor_context": contractor_context,
        "today": today.strftime("%Y-%m-%d"),
    })







def contract_daily_attendance_edit(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser

    contractors = [c[0] for c in CONTRACT_NAME_CHOICES]
    contractor_choices = CONTRACT_NAME_CHOICES
    shifts = [s[0] for s in SHIFT_CHOICES]
    shift_choices = SHIFT_CHOICES

    departments = [
        ("A Block", "a_block"),
        ("B Block", "b_block"),
        ("C Block", "c_block"),
        ("D Block", "d_block"),
        ("PKG", "pkg"),
        ("Pilot", "pilot"),
        ("E Block- 17 Production", "e_block_17_production"),
        ("MEE/ETP", "mee_etp"),
        ("RO Plant", "ro_plant"),
        ("MNTS", "mnts"),
        ("ELE", "ele"),
        ("INST", "inst"),
        ("RM/ENGG 16 - 17 & 18", "rm_engg_16_17_18"),
        ("QC & PD", "qc_pd"),
        ("Boiler", "boiler"),
        ("Dozer Driver", "dozer_driver"),
        ("HouseKeeping 16 - 17 & 18", "housekeeping_16_17_18"),
        ("Office Boy", "office_boy"),
        ("Gardenar", "gardenar"),
        ("OHC", "ohc"),
        ("Painting", "painting"),
        ("MNTS-E 17", "mnts_e17"),
        ("ELE- E-17", "ele_e17"),
        ("INST-E-17", "inst_e17"),
    ]

    edit_date = request.GET.get('date') or request.POST.get('date') or date.today()
    if isinstance(edit_date, str):
        edit_date = date.fromisoformat(edit_date)

    if request.method == "POST":
        # Removed ContractorDailyRequirement update block

        # Save ContractorManpowerAttendance (contractor/shift actuals)
        for contractor in contractors:
            for shift in shifts:
                save_kwargs = {
                    'date': edit_date,
                    'contractor': contractor,
                    'shift': shift,
                }
                for dept_display, dept_field in departments:
                    value = request.POST.get(f'{contractor}_{shift}_{dept_field}', 0) or 0
                    save_kwargs[dept_field] = value
                ContractorManpowerAttendance.objects.update_or_create(
                    date=edit_date,
                    contractor=contractor,
                    shift=shift,
                    defaults=save_kwargs
                )
        messages.success(request, "Contractor manpower attendance updated successfully.")
        return redirect("contract_daily_attendance_edit")  # Redirect back to edit page or change as needed

    # Prepare context for GET
    att_map = {}
    for att in ContractorManpowerAttendance.objects.filter(date=edit_date):
        att_map[(att.contractor, att.shift)] = att

    contractor_context = []
    for contractor, contractor_label in contractor_choices:
        shifts_context = []
        for shift, shift_label in shift_choices:
            dept_values = {}
            att = att_map.get((contractor, shift))
            for dept_display, dept_field in departments:
                dept_values[dept_field] = getattr(att, dept_field) if att else ''
            shifts_context.append({
                'shift': shift,
                'shift_label': shift_label,
                'dept_values': dept_values,
            })
        contractor_context.append({
            'contractor': contractor,
            'contractor_label': contractor_label,
            # Removed 'required_total' key as no more needed
            'shifts': shifts_context,
        })

    return render(request, "contract/contractor_daily_edit.html", {
        'user_groups': user_groups,
        'is_superuser': is_superuser,
        "departments": departments,
        "contractor_context": contractor_context,
        "edit_date": edit_date.strftime("%Y-%m-%d"),
    })

def contract_shiftwise_report(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser

    # Use report_mode to decide which filter to use
    report_mode = request.GET.get('report_mode', 'daily')
    date_str = request.GET.get('date', '')
    month_str = request.GET.get('month', '')
    mode = 'daily' if report_mode == 'daily' else 'monthly'
    selected_date = None
    selected_year = None
    selected_month = None

    if mode == 'daily':
        if date_str:
            try:
                selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except Exception:
                selected_date = now().date()
        else:
            selected_date = now().date()
    else:
        if month_str:
            try:
                selected_year, selected_month = map(int, month_str.split('-'))
            except Exception:
                today = now().date()
                selected_year, selected_month = today.year, today.month
        else:
            today = now().date()
            selected_year, selected_month = today.year, today.month

    # Mapping of display names to actual model field names
    department_field_map = {
        "A-Block": "a_block",
        "B-Block": "b_block",
        "C-Block": "c_block",
        "D-Block": "d_block",
        "PKG": "pkg",
        "Pilot": "pilot",
        "E Block- 17 Production": "e_block_17_production",
        "MEE/ETP": "mee_etp",
        "RO Plant": "ro_plant",
        "MNTS": "mnts",
        "ELE": "ele",
        "INST": "inst",
        "RM/ENGG 16 - 17 & 18": "rm_engg_16_17_18",
        "QC & PD": "qc_pd",
        "Boiler": "boiler",
        "Dozer Driver": "dozer_driver",
        "HouseKeeping 16 - 17 & 18": "housekeeping_16_17_18",
        "Office Boy": "office_boy",
        "Gardenar": "gardenar",
        "OHC": "ohc",
        "Painting": "painting",
        "MNTS-E 17": "mnts_e17",
        "ELE- E-17": "ele_e17",
        "INST-E-17": "inst_e17",
    }

    departments = DepartmentManpowerRequirement.objects.all().order_by('id')
    contractors = [c[0] for c in CONTRACT_NAME_CHOICES]
    shifts = [s[0] for s in SHIFT_CHOICES]

    if mode == 'daily':
        table = []
        grand_totals = {c: {sh: 0 for sh in shifts} for c in contractors}
        total_required = 0
        total_actual = 0

        overall_shift_totals = {sh: 0 for sh in shifts}

        for dept in departments:
            dept_row = {
                "dept": dept.department_name,
                "required": dept.required_manpower,
            }
            row_actual = 0
            dept_shift_totals = {sh: 0 for sh in shifts}

            for contractor in contractors:
                contractor_total = 0
                for shift in shifts:
                    att = ContractorManpowerAttendance.objects.filter(
                        date=selected_date,
                        contractor=contractor,
                        shift=shift
                    ).first()
                    value = 0
                    if att:
                        field_name = department_field_map.get(dept.department_name)
                        if field_name:
                            value = getattr(att, field_name, 0) or 0
                    key = f"{contractor}_{shift}"
                    dept_row[key] = value
                    grand_totals[contractor][shift] += value
                    dept_shift_totals[shift] += value
                    contractor_total += value
                dept_row[f"{contractor}_ttl"] = contractor_total
                row_actual += contractor_total

            for shift in shifts:
                dept_row[f"grand_{shift}"] = dept_shift_totals[shift]
                overall_shift_totals[shift] += dept_shift_totals[shift]
            dept_row["grand_ttl"] = sum(dept_shift_totals.values())

            dept_row["row_total"] = row_actual
            dept_row["gap"] = row_actual - dept.required_manpower
            total_required += dept.required_manpower
            total_actual += row_actual
            table.append(dept_row)

        contractor_col_totals = {}
        for contractor in contractors:
            contractor_col_totals[contractor] = {
                "shift_totals": [grand_totals[contractor][sh] for sh in shifts],
                "ttl": sum(grand_totals[contractor].values())
            }

        grand_row = {
            "dept": "Grand Total",
            "required": total_required,
            "row_total": total_actual,
            "gap": total_actual - total_required,
        }
        for contractor in contractors:
            for shift in shifts:
                grand_row[f"{contractor}_{shift}"] = grand_totals[contractor][shift]
            grand_row[f"{contractor}_ttl"] = contractor_col_totals[contractor]["ttl"]

        for shift in shifts:
            grand_row[f"grand_{shift}"] = overall_shift_totals[shift]
        grand_row["grand_ttl"] = sum(overall_shift_totals.values())

        table.append(grand_row)

        # Calculate total per contractor across all shifts and departments for the day
        contractor_daily_totals = {}
        for contractor in contractors:
            total_for_contractor = 0
            for shift in shifts:
                for dept in departments:
                    att = ContractorManpowerAttendance.objects.filter(
                        date=selected_date,
                        contractor=contractor,
                        shift=shift
                    ).first()
                    if att:
                        field_name = department_field_map.get(dept.department_name)
                        if field_name:
                            total_for_contractor += getattr(att, field_name, 0) or 0
            contractor_daily_totals[contractor] = total_for_contractor

        context = {
            'user_groups': user_groups,
            'is_superuser': is_superuser,
            "mode": mode,
            "date": selected_date.strftime("%Y-%m-%d"),
            "departments": departments,
            "contractors": contractors,
            "contractor_choices": CONTRACT_NAME_CHOICES,
            "shifts": shifts,
            "shift_labels": [dict(SHIFT_CHOICES)[sh] for sh in shifts],
            "table": table,
            "contractor_daily_totals": contractor_daily_totals,
        }

    else:
        # Monthly logic unchanged
        production_names = [
            'A-Block', 'B-Block', 'C-Block', 'D-Block', 'PKG', 'E Block- 17 Production'
        ]
        def normalize(name):
            return name.strip().replace("-", " ").replace("_", " ").replace("  ", " ").lower()
        norm_prod_names = set(normalize(n) for n in production_names)

        production_depts = [dept for dept in departments if normalize(dept.department_name) in norm_prod_names]
        service_depts = [dept for dept in departments if normalize(dept.department_name) not in norm_prod_names]
        days_in_month = monthrange(selected_year, selected_month)[1]
        dates = [date(selected_year, selected_month, d) for d in range(1, days_in_month + 1)]

        attendance_matrix = {dept.department_name: {d: 0 for d in dates} for dept in departments}
        required_map = {dept.department_name: dept.required_manpower for dept in departments}

        for dept in departments:
            for day in dates:
                total = 0
                for contractor in contractors:
                    for shift in shifts:
                        att = ContractorManpowerAttendance.objects.filter(
                            date=day,
                            contractor=contractor,
                            shift=shift
                        ).first()
                        if att:
                            field_name = department_field_map.get(dept.department_name)
                            if field_name:
                                total += getattr(att, field_name, 0) or 0
                attendance_matrix[dept.department_name][day] = total

        production_depts = [dept for dept in departments if dept.department_name in production_names]
        service_depts = [dept for dept in departments if dept.department_name not in production_names]

        def build_table(dept_list):
            table = []
            for dept in dept_list:
                row = {
                    "dept": dept.department_name,
                    "required": required_map[dept.department_name],
                    "days": [],
                    "total": 0,
                    "avg": 0,
                    "gap": 0,
                    "percents": [],
                }
                total_actual = 0
                for d in dates:
                    actual = attendance_matrix[dept.department_name][d]
                    row["days"].append(actual)
                    total_actual += actual
                row["total"] = total_actual
                row["avg"] = round(total_actual / len(dates), 1) if dates else 0
                row["gap"] = total_actual - (row["required"] * len(dates))
                for val in row["days"]:
                    pct = round(100 * val / row["required"]) if row["required"] else 0
                    row["percents"].append(pct)
                table.append(row)
            return table

        production_table = build_table(production_depts)
        service_table = build_table(service_depts)

        def calc_section_totals(table):
            days_count = len(dates)
            total_required = sum(row['required'] for row in table)
            daily_sum = [sum(row['days'][i] for row in table) for i in range(days_count)]
            avg = round(sum(daily_sum) / days_count, 1) if days_count else 0
            pct_row = [round(100 * daily_sum[i] / total_required) if total_required else 0 for i in range(days_count)]
            return {
                'total_required': total_required,
                'daily_sum': daily_sum,
                'avg': avg,
                'pct_row': pct_row,
            }

        prod_totals = calc_section_totals(production_table)
        serv_totals = calc_section_totals(service_table)

        context = {
            'user_groups': user_groups,
            'is_superuser': is_superuser,
            "mode": mode,
            "month": f"{selected_year}-{selected_month:02d}",
            "dates": dates,
            "production_table": production_table,
            "service_table": service_table,
            "prod_totals": prod_totals,
            "serv_totals": serv_totals,
        }

    return render(request, "contract/contractor_shiftwise_report.html", context)




def contract_shiftwise_report_excel(request):
    # Get report mode and date/month params
    report_mode = request.GET.get('report_mode', 'daily')
    date_str = request.GET.get('date', '')
    month_str = request.GET.get('month', '')
    mode = 'daily' if report_mode == 'daily' else 'monthly'
    selected_date = None
    selected_year = None
    selected_month = None

    if mode == 'daily':
        if date_str:
            try:
                selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except Exception:
                selected_date = date.today()
        else:
            selected_date = date.today()
    else:
        if month_str:
            try:
                selected_year, selected_month = map(int, month_str.split('-'))
            except Exception:
                today = date.today()
                selected_year, selected_month = today.year, today.month
        else:
            today = date.today()
            selected_year, selected_month = today.year, today.month

    department_field_map = {
        "A-Block": "a_block",
        "B-Block": "b_block",
        "C-Block": "c_block",
        "D-Block": "d_block",
        "PKG": "pkg",
        "Pilot": "pilot",
        "E Block- 17 Production": "e_block_17_production",
        "MEE/ETP": "mee_etp",
        "RO Plant": "ro_plant",
        "MNTS": "mnts",
        "ELE": "ele",
        "INST": "inst",
        "RM/ENGG 16 - 17 & 18": "rm_engg_16_17_18",
        "QC & PD": "qc_pd",
        "Boiler": "boiler",
        "Dozer Driver": "dozer_driver",
        "HouseKeeping 16 - 17 & 18": "housekeeping_16_17_18",
        "Office Boy": "office_boy",
        "Gardenar": "gardenar",
        "OHC": "ohc",
        "Painting": "painting",
        "MNTS-E 17": "mnts_e17",
        "ELE- E-17": "ele_e17",
        "INST-E-17": "inst_e17",
    }

    departments = DepartmentManpowerRequirement.objects.all().order_by('id')
    contractors = [c[0] for c in CONTRACT_NAME_CHOICES]
    shifts = [s[0] for s in SHIFT_CHOICES]

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Report")

    bold_format = workbook.add_format({'bold': True})
    number_format = workbook.add_format({'num_format': '0.00'})
    red_bold = workbook.add_format({'bold': True, 'font_color': 'red'})
    blue_bold = workbook.add_format({'bold': True, 'font_color': 'blue'})
    green_bold = workbook.add_format({'bold': True, 'font_color': 'green'})

    if mode == 'daily':
        # Write headers
        worksheet.write(0, 0, "Department", bold_format)
        worksheet.write(0, 1, "Required", bold_format)

        col = 2
        for contractor in contractors:
            for shift in shifts:
                worksheet.write(0, col, f"{contractor} - {shift}", bold_format)
                col += 1
            worksheet.write(0, col, f"{contractor} Total", bold_format)
            col += 1

        worksheet.write(0, col, "Row Total", bold_format)
        worksheet.write(0, col + 1, "Gap (+/-)", bold_format)

        # Prepare accumulators for grand totals
        grand_totals = {}
        for contractor in contractors:
            for shift in shifts:
                grand_totals[f"{contractor}_{shift}"] = 0
            grand_totals[f"{contractor}_total"] = 0
        grand_totals["row_total"] = 0
        grand_totals["gap_total"] = 0

        # Write data rows
        row_index = 1
        for dept in departments:
            worksheet.write(row_index, 0, dept.department_name)
            worksheet.write(row_index, 1, dept.required_manpower)
            col = 2

            row_total = 0
            for contractor in contractors:
                contractor_total = 0
                for shift in shifts:
                    att = ContractorManpowerAttendance.objects.filter(
                        date=selected_date,
                        contractor=contractor,
                        shift=shift
                    ).first()
                    value = 0
                    if att:
                        field_name = department_field_map.get(dept.department_name)
                        if field_name:
                            value = getattr(att, field_name, 0) or 0
                    worksheet.write(row_index, col, value, number_format)
                    grand_totals[f"{contractor}_{shift}"] += value
                    contractor_total += value
                    col += 1
                worksheet.write(row_index, col, contractor_total, number_format)
                grand_totals[f"{contractor}_total"] += contractor_total
                col += 1
                row_total += contractor_total

            worksheet.write(row_index, col, row_total, number_format)
            worksheet.write(row_index, col + 1, row_total - dept.required_manpower, number_format)

            grand_totals["row_total"] += row_total
            grand_totals["gap_total"] += (row_total - dept.required_manpower)

            row_index += 1

        # Write Grand Total row
        worksheet.write(row_index, 0, "Grand Total", bold_format)
        worksheet.write(row_index, 1, "", bold_format)  # blank for required column

        col = 2
        for contractor in contractors:
            for shift in shifts:
                worksheet.write(row_index, col, grand_totals[f"{contractor}_{shift}"], number_format)
                col += 1
            worksheet.write(row_index, col, grand_totals[f"{contractor}_total"], number_format)
            col += 1

        worksheet.write(row_index, col, grand_totals["row_total"], number_format)
        worksheet.write(row_index, col + 1, grand_totals["gap_total"], number_format)

    else:
        # Monthly mode with Production and Service area sections + summary rows
        production_names = [
            'A-Block', 'B-Block', 'C-Block', 'D-Block', 'PKG', 'E Block- 17 Production'
        ]

        def normalize(name):
            return name.strip().replace("-", " ").replace("_", " ").replace("  ", " ").lower()

        norm_prod_names = set(normalize(n) for n in production_names)

        days_in_month = monthrange(selected_year, selected_month)[1]
        dates = [date(selected_year, selected_month, d) for d in range(1, days_in_month + 1)]

        # Build attendance matrix
        attendance_matrix = {dept.department_name: {d: 0 for d in dates} for dept in departments}
        for dept in departments:
            for day in dates:
                total = 0
                for contractor in contractors:
                    for shift in shifts:
                        att = ContractorManpowerAttendance.objects.filter(
                            date=day,
                            contractor=contractor,
                            shift=shift
                        ).first()
                        if att:
                            field_name = department_field_map.get(dept.department_name)
                            if field_name:
                                total += getattr(att, field_name, 0) or 0
                attendance_matrix[dept.department_name][day] = total

        production_depts = [dept for dept in departments if normalize(dept.department_name) in norm_prod_names]
        service_depts = [dept for dept in departments if normalize(dept.department_name) not in norm_prod_names]

        def build_table(dept_list):
            table = []
            for dept in dept_list:
                row = {
                    "dept": dept.department_name,
                    "required": dept.required_manpower,
                    "days": [],
                    "total": 0,
                    "avg": 0,
                    "gap": 0,
                    "percents": [],
                }
                total_actual = 0
                for d in dates:
                    actual = attendance_matrix[dept.department_name][d]
                    row["days"].append(actual)
                    total_actual += actual
                row["total"] = total_actual
                row["avg"] = round(total_actual / len(dates), 1) if dates else 0
                row["gap"] = total_actual - (row["required"] * len(dates))
                for val in row["days"]:
                    pct = round(100 * val / row["required"]) if row["required"] else 0
                    row["percents"].append(pct)
                table.append(row)
            return table

        production_table = build_table(production_depts)
        service_table = build_table(service_depts)

        def calc_section_totals(table):
            days_count = len(dates)
            total_required = sum(row['required'] for row in table)
            daily_sum = [sum(row['days'][i] for row in table) for i in range(days_count)]
            avg = round(sum(daily_sum) / days_count, 1) if days_count else 0
            pct_row = [round(100 * daily_sum[i] / total_required) if total_required else 0 for i in range(days_count)]
            return {
                'total_required': total_required,
                'daily_sum': daily_sum,
                'avg': avg,
                'pct_row': pct_row,
            }

        prod_totals = calc_section_totals(production_table)
        serv_totals = calc_section_totals(service_table)

        # Start writing Production Manpower section
        worksheet.write(0, 0, "Production Manpower", blue_bold)
        row_index = 2

        worksheet.write(row_index, 0, "Dept", bold_format)
        worksheet.write(row_index, 1, "Required", bold_format)
        for i, d in enumerate(dates):
            worksheet.write(row_index, i + 2, d.day, bold_format)
        worksheet.write(row_index, len(dates) + 2, "Avg", bold_format)
        row_index += 1

        for row in production_table:
            worksheet.write(row_index, 0, row["dept"])
            worksheet.write(row_index, 1, row["required"])
            for i, val in enumerate(row["days"]):
                worksheet.write(row_index, i + 2, val, number_format)
            worksheet.write(row_index, len(dates) + 2, row["avg"], number_format)
            row_index += 1

            # Percentage row
            for i, pct in enumerate(row["percents"]):
                worksheet.write(row_index, i + 2, f"{pct}%", red_bold)
            row_index += 1

        # Totals rows
        worksheet.write(row_index, 0, "Total required in production", bold_format)
        worksheet.write(row_index, 1, prod_totals['total_required'], bold_format)
        for i, val in enumerate(prod_totals['daily_sum']):
            worksheet.write(row_index, i + 2, val, bold_format)
        worksheet.write(row_index, len(dates) + 2, prod_totals['avg'], bold_format)
        row_index += 1

        worksheet.write(row_index, 0, "% of Total requirement (prod)", bold_format)
        worksheet.write(row_index, 1, "")
        for i, pct in enumerate(prod_totals['pct_row']):
            worksheet.write(row_index, i + 2, f"{pct}%", red_bold)
        row_index += 2  # Spacer row

        # Service Area Manpower section
        worksheet.write(row_index, 0, "Service Area Manpower", green_bold)
        row_index += 2

        worksheet.write(row_index, 0, "Dept", bold_format)
        worksheet.write(row_index, 1, "Required", bold_format)
        for i, d in enumerate(dates):
            worksheet.write(row_index, i + 2, d.day, bold_format)
        worksheet.write(row_index, len(dates) + 2, "Avg", bold_format)
        row_index += 1

        for row in service_table:
            worksheet.write(row_index, 0, row["dept"])
            worksheet.write(row_index, 1, row["required"])
            for i, val in enumerate(row["days"]):
                worksheet.write(row_index, i + 2, val, number_format)
            worksheet.write(row_index, len(dates) + 2, row["avg"], number_format)
            row_index += 1

            # Percentage row
            for i, pct in enumerate(row["percents"]):
                worksheet.write(row_index, i + 2, f"{pct}%", red_bold)
            row_index += 1

        # Totals rows
        worksheet.write(row_index, 0, "Total required in service area", bold_format)
        worksheet.write(row_index, 1, serv_totals['total_required'], bold_format)
        for i, val in enumerate(serv_totals['daily_sum']):
            worksheet.write(row_index, i + 2, val, bold_format)
        worksheet.write(row_index, len(dates) + 2, serv_totals['avg'], bold_format)
        row_index += 1

        worksheet.write(row_index, 0, "% of Total requirement (serv)", bold_format)
        worksheet.write(row_index, 1, "")
        for i, pct in enumerate(serv_totals['pct_row']):
            worksheet.write(row_index, i + 2, f"{pct}%", red_bold)

    workbook.close()
    output.seek(0)

    filename = f"contract_shiftwise_report_{mode}_{date.today()}.xlsx"
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response





#==============================================================================================================




from django.shortcuts import render, redirect
from .forms import ContractorWorkerEntryForm,ContractorWorkerEntryFormSet,ContractorWorkerEntryFormSet
from .models import ContractorWorker
from django.db.models import Sum
from datetime import datetime
from django.shortcuts import redirect, get_list_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required



@login_required
def contractor_worker_entry_add(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser
    # Get date from GET or default to today
    date_value = request.GET.get('date') or datetime.today().strftime('%Y-%m-%d')

    if request.method == 'POST':
        formset = ContractorWorkerEntryFormSet(request.POST)
        if formset.is_valid():
            shared_date = request.POST.get('shared_date')
            for form in formset:
                if not form.cleaned_data.get('DELETE', False):
                    form.instance.date = shared_date
            formset.save()
            # Add success message here
            messages.success(request, "Contractor worker entries added successfully.")
            return redirect(f"{request.path}?date={shared_date}")
    else:
        # Start empty formset on GET
        formset = ContractorWorkerEntryFormSet(queryset=ContractorWorker.objects.none())

    context = {
        'formset': formset,
        'date_value': date_value,
        'user_groups': user_groups,
        'is_superuser': is_superuser,
    }
    return render(request, 'contract1/contractorworkerentry_add.html', context)



@login_required
def contractor_worker_entry_list(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser
    # Get filter params
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    # Base queryset
    dates_qs = ContractorWorker.objects.all()

    # Filter by date range if provided
    if from_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            dates_qs = dates_qs.filter(date__gte=from_date_obj)
        except ValueError:
            pass  # invalid date ignored

    if to_date:
        try:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            dates_qs = dates_qs.filter(date__lte=to_date_obj)
        except ValueError:
            pass  # invalid date ignored

    # Aggregate total emp_count per date
    date_totals = dates_qs.values('date').annotate(total_emp=Sum('emp_count')).order_by('-date')

    context = {
        'date_totals': date_totals,
        'from_date': from_date or '',
        'to_date': to_date or '',
        'user_groups': user_groups,
        'is_superuser': is_superuser,
    }
    return render(request, 'contract1/contractorworkerentry_list.html', context)



@login_required
def contractor_worker_entry_edit(request, date_str):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser

    try:
        edit_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return redirect('contractor_worker_entry_add')

    queryset = ContractorWorker.objects.filter(date=edit_date)

    if request.method == 'POST':
        formset = ContractorWorkerEntryFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            for form in formset:
                if not form.cleaned_data.get('DELETE', False):
                    form.instance.date = edit_date
            formset.save()
            # Add success message here
            messages.success(request, "Contractor worker entries updated successfully.")
            return redirect('contractor_worker_entry_edit', date_str=date_str)
        else:
            print(formset.errors)  # Debug errors
    else:
        formset = ContractorWorkerEntryFormSet(queryset=queryset)

    context = {
        'formset': formset,
        'date_value': edit_date.strftime('%Y-%m-%d'),
        'user_groups': user_groups,
        'is_superuser': is_superuser,
    }
    return render(request, 'contract1/edit_contractorworker.html', context)



@login_required
def contractor_worker_entry_delete(request, date_str):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser
    """
    Deletes all ContractorWorkerEntry records for the specified date.
    """
    try:
        del_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Invalid date format.")
        return redirect('contractor_worker_entry_list')

    if request.method == 'POST':
        entries = ContractorWorker.objects.filter(date=del_date)
        count = entries.count()
        if count > 0:
            entries.delete()
            messages.success(request, f"Deleted {count} entries for date {del_date}.")
        else:
            messages.info(request, "No entries found for the specified date.")
        return redirect('contractor_worker_entry_list')



@login_required
def contractor_worker_entry_detail(request, date_str):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser
    try:
        detail_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return redirect('contractor_worker_entry_list')

    entries = ContractorWorker.objects.filter(date=detail_date)

    contractor_counts = entries.values('contractor_name').annotate(total_emp=Sum('emp_count')).order_by('contractor_name')
    shift_counts = entries.values('shift').annotate(total_emp=Sum('emp_count')).order_by('shift')
    location_counts = entries.values('location').annotate(total_emp=Sum('emp_count')).order_by('location')
    department_counts = entries.values('department').annotate(total_emp=Sum('emp_count')).order_by('department')

    total_emp_count = entries.aggregate(total=Sum('emp_count'))['total'] or 0

    context = {
        'date_value': detail_date.strftime('%Y-%m-%d'),
        'contractor_counts': contractor_counts,
        'shift_counts': shift_counts,
        'location_counts': location_counts,
        'department_counts': department_counts,
        'total_emp_count': total_emp_count,
        'user_groups': user_groups,
        'is_superuser': is_superuser,
    }
    return render(request, 'contract1/contractorworkerentry_detail.html', context)
    
    
    
    
    
    
#==========================Below code is for contract punch in punch out =========================================================


from .models import ContractEmpDepartment,ContractEmployee
from django.db import connection
from django.utils.encoding import escape_uri_path



def get_matched_contract_employees(start_date, end_date, dept_id=None, emp_name=None, shift=None):
    query = """
        SELECT 
            hr.employee_id,
            hr.work_date,
            hr.in_date,
            hr.in_time,
            hr.out_date,
            hr.out_time,
            hr.shift,
            hr.work_hhmm,
            hr.ot_hours,
            hr.double_ot_hours,
            ce.name AS employee_name,
            dept.name AS company
        FROM hr_contract hr
        INNER JOIN contract_employee ce ON hr.employee_id = ce.id
        LEFT JOIN contract_employee_dept dept ON ce.department_id = dept.id
        WHERE hr.work_date >= %s AND hr.work_date <= %s
    """
    params = [start_date, end_date]

    # Only add filter if not 'all' and not blank
    if dept_id and dept_id != 'all' and dept_id != '':
        query += " AND ce.department_id = %s"
        params.append(dept_id)
    if emp_name:
        query += " AND ce.name LIKE %s"
        params.append(f"%{emp_name}%")
    if shift and shift != 'all' and shift != '':
        query += " AND hr.shift = %s"
        params.append(shift)
    query += " ORDER BY hr.employee_id"

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]



def contract_employee_matched_report(request):
    SHIFT_CHOICES = [
        "1st Shift (07:00AM-15:00PM)",
        "General (09:00AM-18:00PM)",
        "2nd Shift (15:00PM-23:00PM)",
        "4th Shift (19:00PM-07:00AM)",
        "Night (23:00PM-07:00AM)",
        "3rd Shift (07:00AM-19:00PM)",  
    ]
    today_str = datetime.now().strftime('%Y-%m-%d')
    start_date = request.GET.get('start_date', today_str)
    end_date = request.GET.get('end_date', today_str)
    dept_id = request.GET.get('department', '')
    emp_name = request.GET.get('employee_name', '').strip()
    shift = request.GET.get('shift', 'all')

    records = get_matched_contract_employees(start_date, end_date, dept_id, emp_name, shift)

    total = len(records)
    total_ot = sum(int(rec['ot_hours'] or 0) for rec in records)
    double_ot = sum(int(rec['double_ot_hours'] or 0) for rec in records)
    total_work_minutes = 0
    for rec in records:
        hhmm = rec.get('work_hhmm')
        if hhmm and ':' in hhmm:
            h, m = [int(x) for x in hhmm.split(':')]
            total_work_minutes += h * 60 + m
    total_work_hhmm = f"{total_work_minutes // 60:02d}:{total_work_minutes % 60:02d}"

    departments = ContractEmpDepartment.objects.order_by('name')

    return render(request, 'contract1/contract_attend_report.html', {
        'records': records,
        'start_date': start_date,
        'end_date': end_date,
        'total': total,
        'total_ot': total_ot,
        'double_ot': double_ot,
        'total_work_hhmm': total_work_hhmm,
        'departments': departments,
        'selected_dept': str(dept_id),
        'employee_name': emp_name,
        'shift_choices': SHIFT_CHOICES,
        'selected_shift': shift,
    })


def contract_employee_attend_report_excel(request):
    SHIFT_CHOICES = [
        "1st Shift (07:00AM-15:00PM)",
        "General (09:00AM-18:00PM)",
        "2nd Shift (15:00PM-23:00PM)",
        "4th Shift (19:00PM-07:00AM)",
        "Night (23:00PM-07:00AM)",
        "3rd Shift (07:00AM-19:00PM)",
    ]
    today_str = datetime.now().strftime('%Y-%m-%d')
    start_date = request.GET.get('start_date', today_str)
    end_date = request.GET.get('end_date', today_str)
    dept_id = request.GET.get('department', '')
    emp_name = request.GET.get('employee_name', '').strip()
    shift = request.GET.get('shift', 'all')

    # Clean up department and shift values BEFORE passing to SQL function!
    if dept_id == 'all' or not dept_id:
        dept_id = ''
    if shift == 'all' or not shift:
        shift = None

    records = get_matched_contract_employees(start_date, end_date, dept_id, emp_name, shift)

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    ws = workbook.add_worksheet('Attendance')

    headers = [
        "Emp Code", "Name", "Company", "Work Date", "In Date", "In Time",
        "Out Date", "Out Time", "Shift", "Work HHMM", "OT Hours", "Double OT"
    ]
    ws.write_row(0, 0, headers)
    for rowidx, rec in enumerate(records, 1):
        ws.write(rowidx, 0, rec.get('employee_id'))
        ws.write(rowidx, 1, rec.get('employee_name'))
        ws.write(rowidx, 2, rec.get('company'))
        ws.write(rowidx, 3, str(rec.get('work_date')))
        ws.write(rowidx, 4, str(rec.get('in_date')))
        ws.write(rowidx, 5, rec.get('in_time'))
        ws.write(rowidx, 6, str(rec.get('out_date')))
        ws.write(rowidx, 7, rec.get('out_time'))
        ws.write(rowidx, 8, rec.get('shift'))
        ws.write(rowidx, 9, rec.get('work_hhmm'))
        ws.write(rowidx, 10, rec.get('ot_hours'))
        ws.write(rowidx, 11, rec.get('double_ot_hours'))
    workbook.close()
    output.seek(0)

    filename = f"Contract_Attendance_{start_date}_to_{end_date}.xlsx"
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{escape_uri_path(filename)}"'
    return response    