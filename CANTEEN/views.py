from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from datetime import time,datetime, timedelta
from .models import Employee, Department, Shift, Attendance
from .utils import determine_shift
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from datetime import timedelta, datetime, time
import pytz
from collections import Counter
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Count
from django.utils.timezone import make_aware, is_naive
from collections import defaultdict
import xlsxwriter
import io

# Set your local timezone
LOCAL_TIMEZONE = pytz.timezone("Asia/Kolkata")


def sync_attendance_from_device():
    """
    Fetch attendance records from the ZKTeco device and update the DB.
    Returns sync logs as a list of messages.
    """
    sync_logs = []
    try:
        from zk import ZK, const
    except ImportError:
        sync_logs.append("python-zk not installed.")
        return sync_logs

    ip_address = "192.168.0.30"
    port = 4370

    try:
        zk = ZK(ip_address, port=port, timeout=5, password=0, force_udp=False, ommit_ping=False)
        conn = zk.connect()
        conn.disable_device()

        attendances = conn.get_attendance()
        with transaction.atomic():
            for record in attendances:
                emp_id = record.user_id
                punch_time = record.timestamp

                # Device returns naive timestamp as IST; localize accordingly.
                if punch_time.tzinfo is None:
                    punch_time_ist = LOCAL_TIMEZONE.localize(punch_time)
                else:
                    punch_time_ist = punch_time.astimezone(LOCAL_TIMEZONE)

                # Convert to UTC for database storage.
                punch_time_utc = punch_time_ist.astimezone(pytz.utc)

                # Debug log – you may remove or adjust this print/log.
                sync_logs.append(f"Matching shift for IST time: {emp_id, punch_time_ist.strftime('%Y-%m-%d %H:%M:%S')}")

                # Determine shift using IST time.
                shift = determine_shift(punch_time_ist)
                if not shift:
                    sync_logs.append(f"Skipped - No shift matched for {punch_time_ist.strftime('%H:%M:%S')}")
                    continue

                # Find or create the employee.
                employee = Employee.objects.filter(id=emp_id).first()
                if not employee:
                    department = Department.objects.first()
                    if not department:
                        department = Department.objects.create(name="Default Department")
                    employee = Employee.objects.create(
                        id=emp_id,
                        name=f"Employee {emp_id}",
                        employee_type="Unknown",
                        department=department
                    )
                    sync_logs.append(f"Created default employee with ID {emp_id}")

                # Avoid duplicate punch by checking for existing record at the same UTC time.
                if Attendance.objects.filter(employee=employee, punched_at=punch_time_utc).exists():
                    sync_logs.append(f"Duplicate skipped for {employee.name} at {punch_time_ist.strftime('%H:%M:%S')}")
                    continue

                # Check if already punched for this shift today (using IST day).
                punch_date = punch_time_ist.date()
                start_local = datetime.combine(punch_date, time.min)
                end_local = start_local + timedelta(days=1)
                start_utc = LOCAL_TIMEZONE.localize(start_local).astimezone(pytz.utc)
                end_utc = LOCAL_TIMEZONE.localize(end_local).astimezone(pytz.utc)

                if Attendance.objects.filter(
                    employee=employee,
                    shift=shift,
                    punched_at__gte=start_utc,
                    punched_at__lt=end_utc
                ).exists():
                    sync_logs.append(f"{employee.name} already punched for shift {shift.name} on {punch_date}")
                    continue

                # Save the attendance record (using UTC).
                Attendance.objects.create(
                    employee=employee,
                    punched_at=punch_time_utc,
                    meal_type='Meal',
                    shift=shift
                )
                sync_logs.append(f"Attendance saved for {employee.name} at {punch_time_ist.strftime('%H:%M:%S')} IST")

        conn.enable_device()
        conn.disconnect()
        return sync_logs

    except Exception as e:
        sync_logs.append(str(e))
        return sync_logs



def fetch_attendance_from_device(request):
    """
    API endpoint to fetch attendance from the device and update the DB.
    """
    sync_logs = sync_attendance_from_device()
    # print(sync_logs)
    status_code = 200 if "error" not in " ".join(sync_logs).lower() else 500
    return JsonResponse({
        "status": "success" if status_code == 200 else "error",
        "message": f"Attendance sync completed. {len(sync_logs)} entries processed.",
        "logs": sync_logs
    }, status=status_code)


def canteen_dashboard(request):
    # 1) Sync device on every refresh
    sync_logs = sync_attendance_from_device()
    # print(sync_logs)
    # 2) Pull user info
    user_groups     = request.user.groups.values_list('name', flat=True)
    is_superuser    = request.user.is_superuser
    show_admin_panel = is_superuser or (request.user.is_staff and request.user.is_active)

    # 3) Read & parse filter dates
    from_str = request.GET.get("from_date", "").strip()
    to_str   = request.GET.get("to_date", "").strip()

    now_local = datetime.now(LOCAL_TIMEZONE)

    # parse from_date → start_of_day_local
    try:
        if from_str:
            dt = datetime.strptime(from_str, "%Y-%m-%d")
            start_local = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            start_local = LOCAL_TIMEZONE.localize(start_local)
        else:
            start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    except ValueError:
        start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)

    # parse to_date → end_of_day_local
    try:
        if to_str:
            dt = datetime.strptime(to_str, "%Y-%m-%d")
            end_local = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            end_local = LOCAL_TIMEZONE.localize(end_local)
        else:
            end_local = now_local.replace(hour=23, minute=59, second=59, microsecond=999999)
    except ValueError:
        end_local = now_local.replace(hour=23, minute=59, second=59, microsecond=999999)

    # convert to UTC for DB filtering
    start_utc = start_local.astimezone(pytz.utc)
    end_utc   = end_local.astimezone(pytz.utc)

    # 4) filter attendances
    attendances = Attendance.objects.filter(
        punched_at__gte=start_utc,
        punched_at__lte=end_utc
    ).order_by('-punched_at')

    # 5) build charts & cards exactly as before
    shift_counts = Counter(a.shift.name if a.shift else "Unknown" for a in attendances)
    sorted_names = sorted(shift_counts)
    shift_chart_data = {
        'labels': sorted_names,
        'data':   [shift_counts[n] for n in sorted_names]
    }

    all_shifts = Shift.objects.all().order_by('start_time')
    shift_card_data = [{
        'id':         s.id,
        'name':       s.name,
        'start_time': s.start_time,
        'end_time':   s.end_time,
        'count':      shift_counts.get(s.name, 0)
    } for s in all_shifts if shift_counts.get(s.name, 0)]

    week_start = now_local - timedelta(days=7)
    weekly_att = Attendance.objects.filter(
        punched_at__gte=week_start.astimezone(pytz.utc),
        punched_at__lte=end_utc
    )
    wcounts = Counter(a.shift.name if a.shift else "Unknown" for a in weekly_att)
    shift_weekly_chart_data = {
        'labels': sorted(wcounts),
        'data':   [wcounts[n] for n in sorted(wcounts)]
    }

    month_start = now_local - timedelta(days=30)
    monthly_att = Attendance.objects.filter(
        punched_at__gte=month_start.astimezone(pytz.utc),
        punched_at__lte=end_utc
    )
    mcounts = Counter(a.shift.name if a.shift else "Unknown" for a in monthly_att)
    shift_monthly_chart_data = {
        'labels': sorted(mcounts),
        'data':   [mcounts[n] for n in sorted(mcounts)]
    }

    # 6) render with the raw filter strings so inputs stay populated
    return render(request, 'canteen/canteen_dashboard.html', {
        'attendances':               attendances,
        'shift_card_data':           shift_card_data,
        'shift_chart_data':          shift_chart_data,
        'shift_weekly_chart_data':   shift_weekly_chart_data,
        'shift_monthly_chart_data':  shift_monthly_chart_data,
        'user_groups':               user_groups,
        'is_superuser':              is_superuser,
        'show_admin_panel':          show_admin_panel,
        'from_date':                 from_str,
        'to_date':                   to_str,
    })


@csrf_exempt
def update_attendance(request):
    """
    API endpoint to receive attendance data via POST.
    Checks for valid punch time and prevents duplicates.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed.'}, status=405)

    try:
        data = json.loads(request.body)
        # print(data)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON payload.'}, status=400)

    employee_id = data.get('employee_id')
    punched_at_str = data.get('punched_at')
    meal_type = data.get('meal_type', 'Meal')

    if not employee_id or not punched_at_str:
        return JsonResponse({'status': 'error', 'message': 'Missing employee_id or punched_at.'}, status=400)

    try:
        if punched_at_str.endswith('Z'):
            # Replace Z with +00:00 then parse (if needed)
            punched_at_str = punched_at_str[:-1] + '+00:00'

        punched_at = datetime.fromisoformat(punched_at_str)

        # Device returns naive time as IST: so localize to IST if no tzinfo; otherwise, convert
        if punched_at.tzinfo is None:
            punched_at_local = LOCAL_TIMEZONE.localize(punched_at)
        else:
            punched_at_local = punched_at.astimezone(LOCAL_TIMEZONE)

        # Convert to UTC for storing in DB
        punched_at_utc = punched_at_local.astimezone(pytz.utc)

        # Determine shift based on IST time
        shift = determine_shift(punched_at_local)
        if not shift:
            return JsonResponse({'status': 'error', 'message': 'Punch time outside allowed schedule.'}, status=400)

        employee = Employee.objects.filter(id=employee_id).first()
        if not employee:
            return JsonResponse({'status': 'error', 'message': f'Employee with id {employee_id} not found.'}, status=404)

        # Check duplicate punch at exact UTC time
        if Attendance.objects.filter(employee=employee, punched_at=punched_at_utc).exists():
            return JsonResponse({'status': 'error', 'message': 'Duplicate record.'}, status=400)

        # Check duplicate for same shift on same local day
        punch_date = punched_at_local.date()
        start_local = datetime.combine(punch_date, time.min)
        end_local = start_local + timedelta(days=1)
        start_utc = LOCAL_TIMEZONE.localize(start_local).astimezone(pytz.utc)
        end_utc = LOCAL_TIMEZONE.localize(end_local).astimezone(pytz.utc)

        if Attendance.objects.filter(
            employee=employee,
            shift=shift,
            punched_at__gte=start_utc,
            punched_at__lt=end_utc
        ).exists():
            return JsonResponse({'status': 'error', 'message': 'Already punched for this shift today.'}, status=400)

        # Create attendance with UTC time
        new_attendance = Attendance.objects.create(
            employee=employee,
            punched_at=punched_at_utc,
            meal_type=meal_type,
            shift=shift
        )

        return JsonResponse({'status': 'success', 'attendance_id': new_attendance.id})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Internal error: {str(e)}'}, status=500)


@csrf_exempt
def device_push(request):
    """
    API endpoint to push attendance from device.
    Prevents duplicate shift punch and returns employee name if successful.
    """
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Only POST method allowed."}, status=405)

    try:
        data = json.loads(request.body)
        # print('DATA:',data)
        user_id = data.get("UserID")
        punch_time_str = data.get("Timestamp")

        if not user_id or not punch_time_str:
            return JsonResponse({"status": "error", "message": "Missing UserID or Timestamp."}, status=400)

        punch_time = datetime.strptime(punch_time_str, "%Y-%m-%d %H:%M:%S")
        
        # Device returns naive time as IST; localize appropriately
        if punch_time.tzinfo is None:
            punch_time_local = LOCAL_TIMEZONE.localize(punch_time)
        else:
            punch_time_local = punch_time.astimezone(LOCAL_TIMEZONE)
        
        # Convert to UTC for DB storage
        punch_time_utc = punch_time_local.astimezone(pytz.utc)
        
        # Determine shift using IST time
        shift = determine_shift(punch_time_local)
        if not shift:
            return JsonResponse({"status": "error", "message": "Punch time outside allowed schedule."}, status=400)

        employee = Employee.objects.filter(id=user_id).first()
        if not employee:
            return JsonResponse({"status": "error", "message": "Employee not found"}, status=404)

        # Check for duplicate punch for the same shift on the same local day
        punch_date = punch_time_local.date()
        start_local = datetime.combine(punch_date, time.min)
        end_local = start_local + timedelta(days=1)
        start_utc = LOCAL_TIMEZONE.localize(start_local).astimezone(pytz.utc)
        end_utc = LOCAL_TIMEZONE.localize(end_local).astimezone(pytz.utc)

        if Attendance.objects.filter(
            employee=employee,
            shift=shift,
            punched_at__gte=start_utc,
            punched_at__lt=end_utc
        ).exists():
            return JsonResponse({
                "status": "duplicate",
                "message": f"{employee.name} already punched for shift '{shift.name}' on {punch_date}."
            }, status=200)

        # Record attendance with UTC time
        Attendance.objects.create(
            employee=employee,
            punched_at=punch_time_utc,
            meal_type="Meal",
            shift=shift
        )

        return JsonResponse({
            "status": "ok",
            "employee": employee.name,
            "message": f"Attendance saved for {employee.name} at {punch_time_local.strftime('%I:%M %p')}"
        }, status=200)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)




@require_GET
def dashboard_data_api(request):
    now_local = datetime.now(LOCAL_TIMEZONE)
    start_of_today = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_tomorrow = start_of_today + timedelta(days=1)

    # Make sure datetimes are timezone-aware in UTC
    if is_naive(start_of_today):
        start_utc = make_aware(start_of_today, LOCAL_TIMEZONE).astimezone(pytz.utc)
    else:
        start_utc = start_of_today.astimezone(pytz.utc)

    if is_naive(start_of_tomorrow):
        end_utc = make_aware(start_of_tomorrow, LOCAL_TIMEZONE).astimezone(pytz.utc)
    else:
        end_utc = start_of_tomorrow.astimezone(pytz.utc)

    attendances = Attendance.objects.filter(
        punched_at__gte=start_utc,
        punched_at__lt=end_utc
    ).order_by('-punched_at')

    # print(f"[DEBUG] API attendances count: {attendances.count()}")

    shift_counts = Counter(att.shift.name if att.shift else "Unknown" for att in attendances)

    shift_chart_data = {
        'labels': list(shift_counts.keys()),
        'data': list(shift_counts.values()),
    }

    attendance_data = [
        {
            'employee': a.employee.name,
            'department': a.employee.department.name if a.employee.department else "",
            'shift': a.shift.name if a.shift else "Unknown",
            'punched_at': a.punched_at.astimezone(LOCAL_TIMEZONE).strftime("%d %b %Y, %I:%M %p"),
            'location': getattr(a.employee, 'location', 'Unknown'),
        }
        for a in attendances
    ]

    return JsonResponse({
        'shift_chart_data': shift_chart_data,
        'attendances': attendance_data,
    })



@login_required
def canteen_attendance_summary_report(request):
    user_groups  = request.user.groups.values_list("name", flat=True)
    is_superuser = request.user.is_superuser

    today           = datetime.today()
    selected_month  = int(request.GET.get("month",  today.month))
    selected_year   = int(request.GET.get("year",   today.year))
    filter_type     = request.GET.get("filter_type", "monthly")     # daily / monthly
    emp_group       = request.GET.get("emp_group",   "all")         # all / regular / casual

    # ---- date range --------------------------------------------------------
    start_date = datetime(selected_year, selected_month, 1)
    next_month = start_date.replace(day=28) + timedelta(days=4)
    end_date   = next_month - timedelta(days=next_month.day)

    # ---- day headers for daily view ----------------------------------------
    date_headers, cur = [], start_date
    while cur <= end_date:
        date_headers.append(cur.date())
        cur += timedelta(days=1)

    # ---- attendance rows ---------------------------------------------------
    valid_shift_ids = (
        Shift.objects.filter(name__in=["Lunch F", "Lunch G", "Dinner", "Evening Dinner"])
        .values_list("id", flat=True)
    )

    attendances = (
        Attendance.objects.filter(
            punched_at__date__range=(start_date.date(), end_date.date()),
            shift_id__in=valid_shift_ids,
        )
        .values(
            "employee__id",
            "employee__name",
            "employee__employee_type",
            "punched_at__date",
        )
        .annotate(count=Count("id"))
    )

    # ---- arrange counts per employee ---------------------------------------
    data = defaultdict(
        lambda: {
            "employee_name": "",
            "employee_type": "",
            "date_counts": defaultdict(int),
        }
    )

    for row in attendances:
        emp_id                    = row["employee__id"]
        d                         = data[emp_id]
        d["employee_name"]        = row["employee__name"]
        d["employee_type"]        = row["employee__employee_type"] or "Company"
        d["date_counts"][row["punched_at__date"]] += row["count"]

    # ---- helper for rupee values -------------------------------------------
    RATE_COMPANY = 73
    RATE_CASUAL  = 49

    def compute_amounts(emp_type, days_with_meal, extra_meals, total_meals):
        """Return dict with keys: emp, comp, total"""
        if emp_type == "Casual":
            total = total_meals * RATE_CASUAL
            return {"emp": 0, "comp": total, "total": total}

        emp_share  = round(days_with_meal * RATE_COMPANY * 0.40, 2)
        comp_share = round(days_with_meal * RATE_COMPANY * 0.60 +
                           extra_meals  * RATE_COMPANY, 2)
        total      = total_meals * RATE_COMPANY
        return {"emp": emp_share, "comp": comp_share, "total": total}

    # ---- DAILY table --------------------------------------------------------
    final_data = []
    for emp_id, info in data.items():
        # employee-type filter
        if emp_group == "regular" and info["employee_type"] == "Casual":
            continue
        if emp_group == "casual"  and info["employee_type"] != "Casual":
            continue

        counts_by_day   = [info["date_counts"].get(d, 0) for d in date_headers]
        total_meals     = sum(counts_by_day)
        days_with_meal  = sum(1 for c in counts_by_day if c)
        extra_meals     = total_meals - days_with_meal
        amounts         = compute_amounts(info["employee_type"],
                                          days_with_meal, extra_meals, total_meals)

        final_data.append({
            "id":            emp_id,
            "employee_name": info["employee_name"],
            "employee_type": info["employee_type"],
            "date_strings":  [str(c or 0) for c in counts_by_day],
            "meal_count":    total_meals,
            "total":         amounts["total"],
            "contrib_40":    amounts["emp"],
            "contrib_60":    amounts["comp"],
        })

    # ---- DAILY grand totals -------------------------------------------------
    grand_meals      = sum(r["meal_count"] for r in final_data)
    grand_total      = sum(r["total"]      for r in final_data)
    grand_contrib_40 = sum(r["contrib_40"] for r in final_data)
    grand_contrib_60 = sum(r["contrib_60"] for r in final_data)

    grand_day_counts = [
        sum(int(r["date_strings"][i]) for r in final_data)
        for i in range(len(date_headers))
    ] if final_data else [0] * len(date_headers)

    # ---- MONTHLY summary ----------------------------------------------------
    monthly_data = []
    if filter_type == "monthly":
        for emp_id, info in data.items():
            # apply same employee-type filter
            if emp_group == "regular" and info["employee_type"] == "Casual":
                continue
            if emp_group == "casual"  and info["employee_type"] != "Casual":
                continue

            total_meals   = sum(info["date_counts"].values())
            days_with_meal = sum(1 for v in info["date_counts"].values() if v)
            extra_meals   = total_meals - days_with_meal
            amounts       = compute_amounts(info["employee_type"],
                                            days_with_meal, extra_meals, total_meals)

            monthly_data.append({
                "id":            emp_id,
                "employee_name": info["employee_name"],
                "employee_type": info["employee_type"],
                "meal_count":    total_meals,
                "total":         amounts["total"],
                "contrib_40":    amounts["emp"],
                "contrib_60":    amounts["comp"],
            })

        monthly_grand_meals      = sum(r["meal_count"] for r in monthly_data)
        monthly_grand_total      = sum(r["total"]      for r in monthly_data)
        monthly_grand_contrib_40 = sum(r["contrib_40"] for r in monthly_data)
        monthly_grand_contrib_60 = sum(r["contrib_60"] for r in monthly_data)
    else:
        monthly_data               = []
        monthly_grand_meals        = grand_meals
        monthly_grand_total        = grand_total
        monthly_grand_contrib_40   = grand_contrib_40
        monthly_grand_contrib_60   = grand_contrib_60

    # ---- render -------------------------------------------------------------
    months = [(i, datetime(2025, i, 1).strftime("%B")) for i in range(1, 13)]
    years  = [2024, 2025, 2026]

    return render(request, "canteen/canteen_attendance_summary.html", {
        "user_groups":               user_groups,
        "is_superuser":              is_superuser,
        "filter_type":               filter_type,
        "emp_group":                 emp_group,          # ▶︎ for template
        "report_data":               final_data,
        "monthly_data":              monthly_data,
        "date_headers":              date_headers,
        "months":                    months,
        "years":                     years,
        "selected_month":            selected_month,
        "selected_year":             selected_year,
        "grand_meals":               grand_meals,
        "grand_total":               grand_total,
        "grand_contrib_40":          grand_contrib_40,
        "grand_contrib_60":          grand_contrib_60,
        "grand_day_counts":          grand_day_counts,
        "monthly_grand_meals":       monthly_grand_meals,
        "monthly_grand_total":       monthly_grand_total,
        "monthly_grand_contrib_40":  monthly_grand_contrib_40,
        "monthly_grand_contrib_60":  monthly_grand_contrib_60,
    })


@login_required
def download_canteen_excel(request):
    selected_month = int(request.GET.get('month', datetime.today().month))
    selected_year = int(request.GET.get('year', datetime.today().year))
    filter_type = request.GET.get('filter_type', 'monthly')  # default to monthly
    emp_group = request.GET.get('emp_group', 'all')

    start_date = datetime(selected_year, selected_month, 1)
    next_month = start_date.replace(day=28) + timedelta(days=4)
    end_date = next_month - timedelta(days=next_month.day)

    date_headers = []
    current_date = start_date
    while current_date <= end_date:
        date_headers.append(current_date.date())
        current_date += timedelta(days=1)

    valid_shifts = Shift.objects.filter(
        name__in=["Lunch F", "Lunch G", "Dinner", "Evening Dinner"]
    ).values_list('id', flat=True)

    # Also fetch employee_type
    attendances = Attendance.objects.filter(
        punched_at__date__range=(start_date.date(), end_date.date()),
        shift_id__in=valid_shifts
    ).values(
        'employee__id', 'employee__name', 'employee__employee_type', 'punched_at__date'
    ).annotate(count=Count('id'))

    data = defaultdict(lambda: {
        'employee_name': '',
        'employee_type': '',
        'date_counts': defaultdict(int)
    })

    for item in attendances:
        emp_id = item['employee__id']
        emp_name = item['employee__name']
        emp_type = item['employee__employee_type'] or 'Company'
        punch_date = item['punched_at__date']
        data[emp_id]['employee_name'] = emp_name
        data[emp_id]['employee_type'] = emp_type
        data[emp_id]['date_counts'][punch_date] += item['count']

    # === FILTER BY emp_group ===
    def include_row(emp_type):
        emp_type = (emp_type or 'Company').lower()
        if emp_group == 'all':
            return True
        elif emp_group == 'regular':
            return emp_type in ['company', 'trainee', 'guest']
        elif emp_group == 'casual':
            return emp_type == 'casual'
        return True

    RATE_COMPANY = 73
    RATE_CASUAL = 49

    def compute_amounts(emp_type, days_with_meal, extra_meals, total_meals):
        if emp_type == "Casual":
            total = total_meals * RATE_CASUAL
            # Place in company contribution, emp_contrib=0
            return {"emp": 0, "comp": total, "total": total}
        emp_share = round(days_with_meal * RATE_COMPANY * 0.40, 2)
        comp_share = round(days_with_meal * RATE_COMPANY * 0.60 +
                           extra_meals * RATE_COMPANY, 2)
        total = total_meals * RATE_COMPANY
        return {"emp": emp_share, "comp": comp_share, "total": total}

    # =========================
    # MONTHLY SUMMARY (default)
    # =========================
    if filter_type == 'monthly':
        excel_data = []
        for emp_id, info in data.items():
            if not include_row(info['employee_type']):
                continue
            total_meals = sum(info['date_counts'].values())
            days_with_meal = sum(1 for v in info['date_counts'].values() if v > 0)
            extra_meals = total_meals - days_with_meal
            amounts = compute_amounts(info['employee_type'], days_with_meal, extra_meals, total_meals)
            excel_data.append({
                'id': emp_id,
                'employee_name': info['employee_name'],
                'employee_type': info['employee_type'],
                'meal_count': total_meals,
                'contrib_40': amounts['emp'],
                'contrib_60': amounts['comp'],
                'total': amounts['total'],
            })

        grand_meals = sum(row['meal_count'] for row in excel_data)
        grand_total = sum(row['total'] for row in excel_data)
        grand_contrib_40 = sum(row['contrib_40'] for row in excel_data)
        grand_contrib_60 = sum(row['contrib_60'] for row in excel_data)

        # Excel
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Canteen Summary")

        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#C6E0B4', 'align': 'center', 'border': 1})
        total_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFF2CC', 'align': 'center', 'border': 1})

        headers = ['ID', 'Employee Name', 'Employee Type', 'Total Meals', 'Employee Contribution ₹', 'Company Contribution ₹', 'Total ₹']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_fmt)

        for row_num, row in enumerate(excel_data, start=1):
            padded_id = str(row['id']).zfill(5)
            worksheet.write(row_num, 0, padded_id)
            worksheet.write(row_num, 1, row['employee_name'])
            worksheet.write(row_num, 2, row['employee_type'])
            worksheet.write(row_num, 3, row['meal_count'])
            worksheet.write(row_num, 4, row['contrib_40'] if row['employee_type'] != "Casual" else '—')
            worksheet.write(row_num, 5, row['contrib_60'])
            worksheet.write(row_num, 6, row['total'])

        # Grand total row
        total_row = len(excel_data) + 1
        worksheet.write(total_row, 0, '', total_fmt)
        worksheet.write(total_row, 1, 'Grand Total', total_fmt)
        worksheet.write(total_row, 2, '', total_fmt)
        worksheet.write(total_row, 3, grand_meals, total_fmt)
        worksheet.write(total_row, 4, grand_contrib_40, total_fmt)
        worksheet.write(total_row, 5, grand_contrib_60, total_fmt)
        worksheet.write(total_row, 6, grand_total, total_fmt)

        workbook.close()
        output.seek(0)

        filename = f"Canteen_Monthly_Summary_{selected_month:02d}_{selected_year}.xlsx"
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    # =====================
    # DAILY DETAILED EXPORT
    # =====================
    else:
        final_data = []
        for emp_id, info in data.items():
            if not include_row(info['employee_type']):
                continue
            date_values = [info['date_counts'].get(d, 0) for d in date_headers]
            date_strings = [str(v) if v > 0 else "0" for v in date_values]
            meal_count = sum(date_values)
            days_with_meal = sum(1 for v in date_values if v > 0)
            extra_meals = meal_count - days_with_meal
            amounts = compute_amounts(info['employee_type'], days_with_meal, extra_meals, meal_count)
            final_data.append({
                'id': emp_id,
                'employee_name': info['employee_name'],
                'employee_type': info['employee_type'],
                'date_strings': date_strings,
                'meal_count': meal_count,
                'contrib_40': amounts['emp'],
                'contrib_60': amounts['comp'],
                'total': amounts['total'],
            })

        grand_total = sum(row['total'] for row in final_data)
        grand_contrib_40 = sum(row['contrib_40'] for row in final_data)
        grand_contrib_60 = sum(row['contrib_60'] for row in final_data)
        grand_day_counts = []
        for idx in range(len(date_headers)):
            count = sum(int(row['date_strings'][idx]) for row in final_data)
            grand_day_counts.append(count)

        # Excel export
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Attendance Summary")

        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#C6E0B4', 'align': 'center', 'border': 1})
        total_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFF2CC', 'align': 'center', 'border': 1})

        headers = (
            ['ID', 'Employee Name', 'Type'] +
            [d.strftime("%d-%b") for d in date_headers] +
            ['Total Meals', 'Employee Contribution ₹', 'Company Contribution ₹', 'Total ₹']
        )

        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_fmt)

        for row_num, row in enumerate(final_data, start=1):
            padded_id = str(row['id']).zfill(5)
            worksheet.write(row_num, 0, padded_id)
            worksheet.write(row_num, 1, row['employee_name'])
            worksheet.write(row_num, 2, row['employee_type'])
            for col_offset, val in enumerate(row['date_strings'], start=3):
                worksheet.write(row_num, col_offset, val)
            meals_col = 3 + len(date_headers)
            worksheet.write(row_num, meals_col, row['meal_count'])
            worksheet.write(row_num, meals_col + 1, row['contrib_40'] if row['employee_type'] != "Casual" else '—')
            worksheet.write(row_num, meals_col + 2, row['contrib_60'])
            worksheet.write(row_num, meals_col + 3, row['total'])

        # Grand total row
        total_row = len(final_data) + 1
        worksheet.write(total_row, 0, '', total_fmt)
        worksheet.write(total_row, 1, 'Grand Total', total_fmt)
        worksheet.write(total_row, 2, '', total_fmt)
        for c, count in enumerate(grand_day_counts, start=3):
            worksheet.write(total_row, c, count, total_fmt)
        worksheet.write(total_row, meals_col, sum(r['meal_count'] for r in final_data), total_fmt)
        worksheet.write(total_row, meals_col + 1, grand_contrib_40, total_fmt)
        worksheet.write(total_row, meals_col + 2, grand_contrib_60, total_fmt)
        worksheet.write(total_row, meals_col + 3, grand_total, total_fmt)

        workbook.close()
        output.seek(0)

        filename = f"Canteen_Daily_Report_{selected_month:02d}_{selected_year}.xlsx"
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response




@login_required
def attendance_list(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser
    today = datetime.today().date()
    from_str = request.GET.get('from_date', '').strip()
    to_str = request.GET.get('to_date', '').strip()
    name_q = request.GET.get('name', '').strip()
    dept_q = request.GET.get('department', '').strip()
    employee_type_q = request.GET.get('employee_type', '').strip()

    # Parse dates
    try:
        from_date = datetime.strptime(from_str, '%Y-%m-%d').date() if from_str else today
        to_date = datetime.strptime(to_str, '%Y-%m-%d').date() if to_str else today
    except ValueError:
        from_date = to_date = today

    # Filter queryset
    qs = Attendance.objects.filter(punched_at__date__range=(from_date, to_date))
    if name_q:
        qs = qs.filter(employee__name__icontains=name_q)
    if dept_q:
        qs = qs.filter(employee__department_id=dept_q)
    if employee_type_q:
        qs = qs.filter(employee__employee_type=employee_type_q)

    attendances = qs.select_related('employee__department', 'shift').order_by('-punched_at')

    # Count total attendances per employee type and for all attendances
    type_counter = Counter()
    total_attendance = 0
    for att in attendances:
        emp_type = att.employee.employee_type or "Company"
        type_counter[emp_type] += 1
        total_attendance += 1

    # Meta info for cards
    EMP_TYPE_META = {
        "Company":  {"label": "Company", "icon": "fa-user-tie", "bg": "bg-green-50",  "txt": "text-green-700"},
        "Trainee":  {"label": "Trainee", "icon": "fa-person-circle-check", "bg": "bg-yellow-50", "txt": "text-yellow-600"},
        "Guest":    {"label": "Guest",   "icon": "fa-user", "bg": "bg-purple-50", "txt": "text-purple-600"},
        "Casual":   {"label": "Casual",  "icon": "fa-user-clock", "bg": "bg-pink-50", "txt": "text-pink-600"},
    }

    # Build cards for front end (first: Total, then employee types if present)
    type_cards = [
        {
            "type": "Total",
            "count": total_attendance,
            "label": "Total",
            "icon": "fa-users",
            "bg": "bg-blue-50",
            "txt": "text-blue-800",
        }
    ]
    for etype, meta in EMP_TYPE_META.items():
        count = type_counter.get(etype, 0)
        if count:
            type_cards.append({
                "type": etype,
                "count": count,
                "label": meta["label"],
                "icon": meta["icon"],
                "bg": meta["bg"],
                "txt": meta["txt"],
            })

    department_choices = Department.objects.all()
    employee_type_choices = [
        ('', 'All'),
        ('Company', 'Company'),
        ('Trainee', 'Trainee'),
        ('Guest', 'Guest'),
        ('Casual', 'Casual'),
    ]

    return render(request, 'canteen/attendance_list.html', {
        'attendances': attendances,
        'from_date': from_date,
        'to_date': to_date,
        'name_q': name_q,
        'dept_q': dept_q,
        'employee_type_q': employee_type_q,
        'department_choices': department_choices,
        'employee_type_choices': employee_type_choices,
        'user_groups': user_groups,
        'is_superuser': is_superuser,
        'type_cards': type_cards,
    })



@login_required
def attendance_xlsx(request):
    today    = datetime.today().date()
    from_str = request.GET.get('from_date','').strip()
    to_str   = request.GET.get('to_date','').strip()
    name_q   = request.GET.get('name','').strip()
    dept_q   = request.GET.get('department','').strip()
    employee_type_q = request.GET.get('employee_type', '').strip()  # NEW

    try:
        from_date = datetime.strptime(from_str, '%Y-%m-%d').date() if from_str else today
        to_date   = datetime.strptime(to_str,   '%Y-%m-%d').date() if to_str   else today
    except ValueError:
        from_date = to_date = today

    qs = Attendance.objects.select_related('employee__department','shift') \
           .filter(punched_at__date__range=(from_date, to_date))
    if name_q:
        qs = qs.filter(employee__name__icontains=name_q)
    if dept_q:
        qs = qs.filter(employee__department_id=dept_q)
    if employee_type_q:
        qs = qs.filter(employee__employee_type=employee_type_q)
    qs = qs.order_by('punched_at')

    output   = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {
        'in_memory': True,
        'remove_timezone': True,
    })
    sheet = workbook.add_worksheet("Attendance")
    hdr_fmt = workbook.add_format({'bold': True, 'bg_color': '#F0F0F0'})
    headers = ['Employee ID','Employee Name','Department','Employee Type','Punched At','Shift','Meal Type']
    for col, title in enumerate(headers):
        sheet.write(0, col, title, hdr_fmt)

    dt_fmt = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm'})
    for row_idx, att in enumerate(qs, start=1):
        emp_id = str(att.employee.id).zfill(5)
        sheet.write_string(row_idx, 0, emp_id)
        sheet.write_string(row_idx, 1, att.employee.name)
        sheet.write_string(row_idx, 2, att.employee.department.name)
        # EMPLOYEE TYPE COLUMN
        sheet.write_string(row_idx, 3, att.employee.employee_type or '')
        sheet.write_datetime(row_idx, 4, att.punched_at.astimezone(LOCAL_TIMEZONE), dt_fmt)
        sheet.write_string(row_idx, 5, att.shift.name if att.shift else '-')
        sheet.write_string(row_idx, 6, att.meal_type or '-')

    workbook.close()
    output.seek(0)
    fname = f"canteen_attendance_{from_date:%Y%m%d}_{to_date:%Y%m%d}.xlsx"
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{fname}"'
    return response
