from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
import json
from django.http import JsonResponse,HttpResponse
from django.db import connections
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.utils.dateparse import parse_date
from .models import Downtime
from .forms import DowntimeForm,select_block, DEPARTMENT_CHOICES
import pandas as pd
from django.db.models import Sum,Count
from datetime import date, timedelta, datetime



@csrf_exempt
def search_equipment(request):
    """
    AJAX endpoint to search for equipment.
    Returns 'id' as the BOMItemCode (eqpt_id) and 'eqpt_name' for auto-filling the equipment name.
    Filters on Type='Equipment Master' and user input (term) against BOMItemCode or Name.
    """
    term = request.GET.get('term', '')
    like_param = f'%{term}%'

    sql_query = """
    WITH CTE_BOMDetails AS (
        SELECT
            ROW_NUMBER() OVER (ORDER BY det.lBomId, lSeqId) AS [Sr.No],
            TYP.sName AS [ItmType],
            MST.sName AS [ItemName],
            MST.sCode AS [ItemCode],
            BOM.dQty AS [Quantity],
            BOM.dRate AS [Rate],
            BOM.sCode AS [BOMCode],
            BOM.sName AS [BOMName],
            TYP1.sName AS [Type],
            MST1.sCode AS [BOMItemCode],
            MST1.sName AS [Name],
            CASE
                WHEN det.cFlag='P' THEN CAST(det.lUntId AS VARCHAR)
                ELSE u.sName
            END AS [Unit],
            BOM.cTyp AS [Based on],
            dPercentage AS [Percentage],
            CASE
                WHEN det.cFlag='P' THEN det.dQtyPrc
                ELSE det.dQty
            END AS [BOMQty],
            BOM.dCnv AS [BOMCnv],
            det.cFlag AS [cFlag],
            DSG.sCode AS [Resource Type],
            CASE
                WHEN st.lFieldNo=1 THEN BOM.svalue1
                WHEN st.lFieldNo=2 THEN BOM.svalue2
                WHEN st.lFieldNo=3 THEN BOM.svalue3
                WHEN st.lFieldNo=4 THEN BOM.svalue4
                WHEN st.lFieldNo=5 THEN BOM.svalue5
                WHEN st.lFieldNo=6 THEN BOM.svalue6
                WHEN st.lFieldNo=7 THEN BOM.svalue7
                WHEN st.lFieldNo=8 THEN BOM.svalue8
                WHEN st.lFieldNo=9 THEN BOM.svalue9
                WHEN st.lFieldNo=10 THEN BOM.svalue10
                ELSE ''
            END AS [Stock Parameter]
            FROM ITMBOMDET det
            INNER JOIN ITMBOM BOM ON det.lBomId = BOM.lBomId
            INNER JOIN ITMMST MST ON MST.lId = BOM.lId
            INNER JOIN ITMTYP TYP ON TYP.lTypId = BOM.lTypId
            LEFT JOIN ITMMST MST1 ON MST1.lId = det.lBomItm
            LEFT JOIN ITMDET DT ON det.lBomItm = DT.lId
            LEFT JOIN ITMTYP TYP1 ON TYP1.lTypId = DT.lTypId
            LEFT JOIN UNTMST u ON det.lUntId = u.lId
            LEFT OUTER JOIN DSGMST DSG ON DSG.lId = det.lResourceId
            LEFT JOIN STKPRM st ON st.lTypId = TYP.lTypId AND st.bBOM = 1
        )
        SELECT DISTINCT BOMItemCode, Name
        FROM CTE_BOMDetails
        WHERE [Type] = 'Equipment Master'
        AND (BOMItemCode LIKE %s OR Name LIKE %s)
        ORDER BY BOMItemCode;
    """


    with connections['readonly_db'].cursor() as cursor:
        cursor.execute(sql_query, [like_param, like_param])
        rows = cursor.fetchall()

    # Build JSON response in the format that django-select2 expects
    results = []
    for row in rows:
        bom_item_code = row[0]  # BOMItemCode
        eqpt_name = row[1]      # Name
        results.append({
            'id': bom_item_code,    # This will be stored in eqpt_id
            'text': bom_item_code,  # What the user sees in the dropdown
            'eqpt_name': eqpt_name  # Extra data to auto-fill eqpt_name
        })

    return JsonResponse({'results': results})


@csrf_exempt
def search_product(request):
    search_type = request.GET.get('search_type', 'fg_name')
    term = request.GET.get('term', '').strip()
    fg_filter = request.GET.get('fg_filter', '').strip()
    like_term = f"%{term.lower()}%"

    if search_type == 'fg_name':
        sql_query = """
            SELECT MIN(ITM.sCode) AS Output_Item_Code,
                   MIN(ITP.sName) AS Output_Item_Type,
                   ITMCF.sValue AS FG_Name
            FROM txnhdr HDR
            INNER JOIN TXNDET AS DET ON HDR.lId = DET.lId AND DET.cFlag = 'I'
            INNER JOIN ITMMST AS ITM ON DET.lItmId = ITM.lId
            INNER JOIN ITMTYP AS ITP ON ITP.lTypid = DET.lItmtyp
            INNER JOIN ITMCF AS ITMCF ON DET.lItmId = ITMCF.lId AND ITMCF.lFieldNo = 10 AND ITMCF.lLine = 0
            WHERE HDR.lTypid IN (597, 924, 913, 925, 899, 891)
              AND HDR.lCompid = 27
              AND HDR.bDel = 0
              AND ITP.sName NOT IN ('Finished Good')
              AND ITMCF.sValue LIKE %s
            GROUP BY ITMCF.sValue;
        """
    else:  # 'stage_name'
        sql_query = """
            SELECT DISTINCT
                   ITM.sCode AS Output_Item_Code,
                   ITP.sName AS Output_Item_Type,
                   ITM.sName AS Output_Item_Name,
                   ITMCF.sValue AS FG_Name
            FROM txnhdr HDR
            INNER JOIN TXNDET AS DET ON HDR.lId = DET.lId AND DET.cFlag = 'I'
            INNER JOIN ITMMST AS ITM ON DET.lItmId = ITM.lId
            INNER JOIN ITMTYP AS ITP ON ITP.lTypid = DET.lItmtyp
            INNER JOIN ITMCF AS ITMCF ON DET.lItmId = ITMCF.lId AND ITMCF.lFieldNo in(10,8) AND ITMCF.lLine = 0
            WHERE HDR.lTypid IN (597, 924, 913, 925, 899, 891)
              AND HDR.lCompid = 27
              AND HDR.bDel = 0
              AND ITP.sName NOT IN ('Finished Good')
              AND ITM.sName LIKE %s;
        """

    with connections['readonly_db'].cursor() as cursor:
        cursor.execute(sql_query, [like_term])
        rows = cursor.fetchall()

    results = []
    for row in rows:
        if search_type == 'fg_name':
            output_item_code, output_item_type, fg_name = row
            results.append({
                'id': fg_name,
                'text': fg_name,
                'product_code': output_item_code,
                'output_item_type': output_item_type
            })
        else:
            output_item_code, output_item_type, output_item_name, fg_name = row
            if fg_filter and fg_filter.lower() != fg_name.lower():
                continue
            results.append({
                'id': output_item_name,
                'text': output_item_name,
                'product_code': output_item_code,
                'fg_name': fg_name
            })

    return JsonResponse({'results': results})



@csrf_exempt
def search_batch(request):
    """
    AJAX endpoint for batch_no. 
    Filters by the selected stage_name and optionally by a typed term for partial searching.
    """
    stage_name = request.GET.get('stage_name', '')
    term = request.GET.get('term', '')  # user-typed text for partial matching
    like_term = f'%{term}%'

    sql_query = """
        SELECT DISTINCT [O/P Batch No]
        FROM (
            SELECT
                CASE HDR.ltypid
                    WHEN 664 THEN 'Fresh Batch BMR Issue'
                    WHEN 717 THEN 'Cleaning Batch BMR Issue'
                    WHEN 718 THEN 'Reprocess Batch BMR Issue'
                    WHEN 719 THEN 'Blending Batch BMR Issue'
                    WHEN 720 THEN 'Distillation Batch BMR Issue'
                    WHEN 721 THEN 'ETP Batch BMR Issue'
                    ELSE 'NA'
                END AS [BMR Issue Type],
                (SELECT sValue FROM txncf WHERE lid=HDR.lid AND sName='Product Name' AND lLine=0) AS [Product Name],
                (SELECT sValue FROM txncf WHERE lid=HDR.lid AND sName='Batch No' AND lLine=0) AS [O/P Batch No],
                (SELECT sValue FROM txncf WHERE lid=HDR.lid AND sName='Block' AND lLine=0) AS [Block],
                DET.lLine AS [Line No],
                ITP.sName AS [Item Type],
                ITM.sCode AS [Item Code],
                ITM.sName AS [Item Name],
                CONVERT(DECIMAL(18,3), DET.dQty2) AS [Batch Quantity]
            FROM txnhdr HDR
            INNER JOIN TXNDET AS DET ON HDR.lId = DET.lId
            INNER JOIN ITMMST AS ITM ON DET.lItmId = ITM.lId
            INNER JOIN ITMTYP AS ITP ON ITP.lTypid = DET.lItmtyp
            INNER JOIN UNTMST AS UOM ON DET.lUntId = UOM.lId
            WHERE HDR.ltypid IN (664,717,718,719,720,721)
                AND DET.lItmTyp <> 63
                AND DET.bDel <> -2
                AND HDR.bDel <> 1
                AND DET.lClosed <> -2
                AND HDR.lClosed = 0
                AND HDR.lcompid = 27
                AND CONVERT(DATE, CAST(HDR.dtDocDate AS CHAR(8)), 112)
                    BETWEEN '2025-04-01' AND GETDATE()
        ) AS batch_data
        WHERE [Product Name] = %s
          AND [O/P Batch No] LIKE %s
    """

    with connections['readonly_db'].cursor() as cursor:
        # Pass stage_name and the partial term for batch no
        cursor.execute(sql_query, [stage_name, like_term])
        rows = cursor.fetchall()

    results = []
    for row in rows:
        batch_no = row[0]
        results.append({
            'id': batch_no,
            'text': batch_no
        })

    return JsonResponse({'results': results})



@csrf_exempt
def get_bom_details(request):
    """
    POST endpoint that receives JSON with 'eqpt_id' and 'stage_name'.
    Returns:
        - 'bct' -> BOMQty from the query
        - 'bom_qty' -> Quantity from the query
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        eqpt_id = data.get('eqpt_id')      # BOMItemCode
        stage_name = data.get('stage_name')  # ItemName

        if not eqpt_id or not stage_name:
            return JsonResponse({"error": "Missing eqpt_id or stage_name"}, status=400)

        # The same CTE you used, but now with placeholders for eqpt_id and stage_name
        sql_query = """
            WITH CTE_BOMDetails AS (
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY det.lBomId, lSeqId) AS [Sr.No], 
                    TYP.sName AS [ItmType],
                    MST.sName AS [ItemName],
                    MST.sCode AS [ItemCode],
                    BOM.dQty AS [Quantity],
                    BOM.dRate AS [Rate],
                    BOM.sCode AS [BOMCode],
                    BOM.sName AS [BOMName],
                    TYP1.sName AS [Type],
                    MST1.sCode AS [BOMItemCode],
                    MST1.sName AS [Name],
                    CASE 
                        WHEN det.cFlag='P' THEN CAST(det.lUntId AS VARCHAR)
                        ELSE u.sName
                    END AS [Unit],
                    BOM.cTyp AS [Based on],
                    dPercentage AS [Percentage],
                    CASE 
                        WHEN det.cFlag='P' THEN det.dQtyPrc
                        ELSE det.dQty
                    END AS [BOMQty],
                    BOM.dCnv AS [BOMCnv],
                    det.cFlag AS [cFlag],
                    DSG.sCode AS [Resource Type],
                    CASE 
                        WHEN st.lFieldNo=1 THEN BOM.svalue1
                        WHEN st.lFieldNo=2 THEN BOM.svalue2
                        WHEN st.lFieldNo=3 THEN BOM.svalue3
                        WHEN st.lFieldNo=4 THEN BOM.svalue4
                        WHEN st.lFieldNo=5 THEN BOM.svalue5
                        WHEN st.lFieldNo=6 THEN BOM.svalue6
                        WHEN st.lFieldNo=7 THEN BOM.svalue7
                        WHEN st.lFieldNo=8 THEN BOM.svalue8
                        WHEN st.lFieldNo=9 THEN BOM.svalue9
                        WHEN st.lFieldNo=10 THEN BOM.svalue10
                        ELSE ''
                    END AS [Stock Parameter]
                FROM ITMBOMDET det
                INNER JOIN ITMBOM BOM ON det.lBomId = BOM.lBomId
                INNER JOIN ITMMST MST ON MST.lId = BOM.lId
                INNER JOIN ITMTYP TYP ON TYP.lTypId = BOM.lTypId
                LEFT JOIN ITMMST MST1 ON MST1.lId = det.lBomItm
                LEFT JOIN ITMDET DT ON det.lBomItm = DT.lId
                LEFT JOIN ITMTYP TYP1 ON TYP1.lTypId = DT.lTypId
                LEFT JOIN UNTMST u ON det.lUntId = u.lId
                LEFT OUTER JOIN DSGMST DSG ON DSG.lId = det.lResourceId
                LEFT JOIN STKPRM st ON st.lTypId = TYP.lTypId AND st.bBOM = 1
            )
            SELECT 
                Quantity,      -- to populate BOM Qty field
                BOMQty         -- to populate BCT field
            FROM CTE_BOMDetails
            WHERE [Type] = 'Equipment Master'
              AND BOMItemCode = %s
              AND ItemName = %s
            ORDER BY [Sr.No];
        """

        with connections['readonly_db'].cursor() as cursor:
            cursor.execute(sql_query, [eqpt_id, stage_name])
            row = cursor.fetchone()

        if row:
            # row[0] = Quantity, row[1] = BOMQty
            quantity = float(row[0]) if row[0] else 0
            bct = float(row[1]) if row[1] else 0
            return JsonResponse({
                "bom_qty": quantity,  # For the "BOM Qty" field
                "bct": bct           # For the "BCT" field
            })
        else:
            return JsonResponse({"error": "No matching records found"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



@login_required
def add_downtime(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser

    if not request.user.has_perm('PRODUCTION.add_downtime'):
        messages.error(request, "You do not have permission to add downtime records.")
        return redirect('indexpage')

    if request.method == 'POST':
        # Print all POST data
        # print("DEBUG: POST data =", request.POST)

        form = DowntimeForm(request.POST)
        if form.is_valid():
            downtime_obj = form.save()
            messages.success(request, "Downtime record saved successfully!")
            return redirect('add_downtime')
        else:
            # Flag to track if we showed a custom error
            error_displayed = False

            for field, errors in form.errors.items():
                if errors:
                    messages.error(request, f"{field.replace('_', ' ').capitalize()}: {errors[0]}")
                    error_displayed = True
                    break  # Only show first error

            if not error_displayed:
                for error in form.non_field_errors():
                    messages.error(request, error)
                    error_displayed = True
                    break

            # Only show fallback message if no specific one was displayed
            if not error_displayed:
                messages.error(request, "Please correct the errors below.")
    else:
        form = DowntimeForm()

    return render(request, 'downtime/add_downtime_form.html', {
        'form': form,
        'user_groups': user_groups,
        'is_superuser': is_superuser
    })


@login_required
def view_downtime(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser

    if not request.user.has_perm('PRODUCTION.view_downtime'):
        messages.error(request, "You do not have permission to add downtime records.")
        return redirect('indexpage')

    # Permissions
    can_edit_downtime = request.user.has_perm('PRODUCTION.change_downtime')
    can_delete_downtime = request.user.has_perm('PRODUCTION.delete_downtime')
    can_add_downtime = request.user.has_perm('PRODUCTION.add_downtime')
    can_view_downtime = request.user.has_perm('PRODUCTION.view_downtime')

    # Grab filter inputs from GET parameters
    date_filter = request.GET.get('date_filter', '')
    eqpt_id_filter = request.GET.get('eqpt_id_filter', '')
    product_name_filter = request.GET.get('product_name_filter', '')
    downtime_dept_filter = request.GET.get('downtime_dept_filter', '')
    block_filter = request.GET.get('block_filter', '')

    # Base queryset
    downtimes = Downtime.objects.all().order_by('-id')  # ordering by date (modify as needed)

    # Apply filters if provided
    if date_filter:
        parsed_date = parse_date(date_filter)
        if parsed_date:
            downtimes = downtimes.filter(date=parsed_date)
    if eqpt_id_filter:
        downtimes = downtimes.filter(eqpt_id__icontains=eqpt_id_filter)
    if product_name_filter:
        downtimes = downtimes.filter(product_name__icontains=product_name_filter)
    if downtime_dept_filter:
        downtimes = downtimes.filter(downtime_dept__icontains=downtime_dept_filter)
    if block_filter:
        downtimes = downtimes.filter(block__icontains=block_filter)

    # Apply pagination: 10 records per page
    paginator = Paginator(downtimes, 10)
    page = request.GET.get('page')
    try:
        downtimes = paginator.page(page)
    except PageNotAnInteger:
        downtimes = paginator.page(1)
    except EmptyPage:
        downtimes = paginator.page(paginator.num_pages)

    context = {
        'downtimes': downtimes,
        'date_filter': date_filter,
        'eqpt_id_filter': eqpt_id_filter,
        'block_filter': block_filter,
        'downtime_dept_filter': downtime_dept_filter,
        'product_name_filter': product_name_filter,
        'user_groups': user_groups,
        'is_superuser': is_superuser,
        'can_edit_downtime': can_edit_downtime,
        'can_delete_downtime': can_delete_downtime,
        'can_add_downtime': can_add_downtime,
        'can_view_downtime': can_view_downtime,
        'select_block': select_block,
        'DEPARTMENT_CHOICES': DEPARTMENT_CHOICES,
    }
    return render(request, 'downtime/view_downtime.html', context)



@login_required
def view_downtime_detail(request, pk):
    user_groups = request.user.groups.values_list('name', flat=True)  # Check if the user is in HR group
    is_superuser = request.user.is_superuser

    """ View vehicle details (Permission Required: PRODUCTION.view_downtime) """
    if not request.user.has_perm('PRODUCTION.view_downtime'):
        messages.error(request, "You do not have permission to view vehicle records.")
        return redirect('indexpage')
    """
    Displays the details of a single Downtime record.
    """
    downtime = get_object_or_404(Downtime, pk=pk)
    return render(request, 'downtime/view_downtime_detail.html', 
                  {'downtime': downtime,'user_groups':user_groups,'is_superuser':is_superuser})


@login_required
def edit_downtime(request, pk):
    downtime_obj = get_object_or_404(Downtime, pk=pk)
    user_groups = request.user.groups.values_list('name', flat=True)  # Check if the user is in HR group
    is_superuser = request.user.is_superuser

    """ View vehicle details (Permission Required: PRODUCTION.change_downtime) """
    if not request.user.has_perm('PRODUCTION.change_downtime'):
        messages.error(request, "You do not have permission to edit vehicle records.")
        return redirect('indexpage')
    """
    Allows editing an existing Downtime record.
    Uses DowntimeForm to pre-populate fields; on success, redirects to the detail view.
    """
    if request.method == 'POST':
        form = DowntimeForm(request.POST, instance=downtime_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Downtime record updated successfully!")
            return redirect('view_downtime')
        else:
            # Flag to track if we showed a custom error
            error_displayed = False

            for field, errors in form.errors.items():
                if errors:
                    messages.error(request, f"{field.replace('_', ' ').capitalize()}: {errors[0]}")
                    error_displayed = True
                    break  # Only show first error

            if not error_displayed:
                for error in form.non_field_errors():
                    messages.error(request, error)
                    error_displayed = True
                    break

            # Only show fallback message if no specific one was displayed
            if not error_displayed:
                messages.error(request, "Please correct the errors below.")
    else:
        form = DowntimeForm(instance=downtime_obj,initial={'eqpt_id': downtime_obj.eqpt_id})
    return render(request, 'downtime/edit_downtime.html', 
                  {'form': form, 'user_groups':user_groups,'is_superuser':is_superuser})

@login_required
def delete_downtime(request, pk):
    user_groups = request.user.groups.values_list('name', flat=True)  # Check if the user is in HR group
    is_superuser = request.user.is_superuser

    """ View downtime details (Permission Required: PRODUCTION.delete_downtime) """
    if not request.user.has_perm('PRODUCTION.delete_downtime'):
        messages.error(request, "You do not have permission to delete vehicle records.")
        return redirect('indexpage')
    """
    Deletes a Downtime record.
    For GET requests, shows a confirmation page.
    For POST requests, deletes the record and redirects to the listing page.
    """
    downtime = get_object_or_404(Downtime, pk=pk)
    if request.method == 'POST':
        downtime.delete()
        messages.success(request, "Downtime record deleted successfully!")
        return redirect('view_downtime')
    # Render a confirmation page for GET requests
    return render(request,{'downtime': downtime,'user_groups':user_groups,'is_superuser':is_superuser})



@login_required
def export_downtime_excel(request):
    if not request.user.has_perm('PRODUCTION.view_downtime'):
        messages.error(request, "You do not have permission to export downtime records.")
        return redirect('indexpage')

    # Filters
    date_filter = request.GET.get('date_filter', '')
    eqpt_id_filter = request.GET.get('eqpt_id_filter', '')
    block_filter = request.GET.get('block_filter', '')
    downtime_dept_filter = request.GET.get('downtime_dept_filter', '')
    product_name_filter = request.GET.get('product_name_filter', '')

    downtimes = Downtime.objects.all().order_by('-id')

    if date_filter:
        parsed_date = parse_date(date_filter)
        if parsed_date:
            downtimes = downtimes.filter(date=parsed_date)
    if eqpt_id_filter:
        downtimes = downtimes.filter(eqpt_id__icontains=eqpt_id_filter)
    if block_filter:
        downtimes = downtimes.filter(block__icontains=block_filter)
    if downtime_dept_filter:
        downtimes = downtimes.filter(downtime_dept__icontains=downtime_dept_filter)
    if product_name_filter:
        downtimes = downtimes.filter(product_name__icontains=product_name_filter)

    # Prepare DataFrame
    data = downtimes.values(
        'id', 'date', 'eqpt_id', 'eqpt_name', 'product_name', 'product_code', 'batch_no',
        'stage_name', 'block', 'downtime_dept', 'downtime_category', 'reason',
        'start_date', 'start_time', 'end_date', 'end_time', 'total_duration', 'bom_qty', 'bct', 'loss'
    )

    df = pd.DataFrame(data)

    # Rename columns for better presentation
    df.rename(columns={
        'id': 'ID',
        'date': 'Date',
        'eqpt_id': 'Equipment ID',
        'eqpt_name': 'Equipment Name',
        'product_name': 'Product Name',
        'product_code': 'Product Code',
        'batch_no': 'Batch No',
        'stage_name': 'Stage Name',
        'block': 'Block',
        'downtime_dept': 'Downtime Department',
        'downtime_category': 'Downtime Category',
        'reason': 'Reason',
        'start_date': 'Start Date',
        'start_time': 'Start Time',
        'end_date': 'End Date',
        'end_time': 'End Time',
        'total_duration': 'Total Duration (hrs)',
        'bom_qty': 'BOM Qty',
        'bct': 'BCT',
        'loss': 'Loss (Kg)'
    }, inplace=True)

    # Generate Excel in-memory
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=downtime_records.xlsx'

    with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Downtime', index=False)

    return response




@login_required
def downtime_chart_view(request):
    user_groups   = request.user.groups.values_list('name', flat=True)
    is_superuser  = request.user.is_superuser

    # filter dropdown options
    downtime_depts = Downtime.objects.values_list('downtime_dept', flat=True).distinct().order_by('downtime_dept')
    blocks         = Downtime.objects.values_list('block',         flat=True).distinct().order_by('block')
    products       = Downtime.objects.values_list('product_name',  flat=True).distinct().order_by('product_name')
    idle_options   = ['Yes', 'No']

    # read filters + period
    selected_dept    = request.GET.get('downtime_dept', '')
    selected_block   = request.GET.get('block', '')
    selected_product = request.GET.get('product_name', '')
    selected_idle    = request.GET.get('idle', '')
    period           = request.GET.get('period', 'MTD')

    # compute date range
    today = date.today()
    if period == 'Weekly':
        start_dt, end_dt = today - timedelta(days=7), today
    elif period == 'Custom':
        try:
            start_dt = datetime.strptime(request.GET.get('start_date',''), '%Y-%m-%d').date()
        except:
            start_dt = today.replace(day=1)
        try:
            end_dt = datetime.strptime(request.GET.get('end_date',''), '%Y-%m-%d').date()
        except:
            end_dt = today
    else:  # MTD
        start_dt, end_dt = today.replace(day=1), today

    # base queryset + apply all filters
    qs = Downtime.objects.filter(start_date__gte=start_dt, end_date__lte=end_dt)
    if selected_dept:    qs = qs.filter(downtime_dept=selected_dept)
    if selected_block:   qs = qs.filter(block=selected_block)
    if selected_product: qs = qs.filter(product_name=selected_product)
    if selected_idle:    qs = qs.filter(idle=selected_idle)

    # 1️⃣ Bar: aggregate total_duration by block
    agg = (qs.values('block')
             .annotate(total_duration=Sum('total_duration'))
             .order_by('block'))
    bar_labels = [row['block'] for row in agg]
    bar_data   = [float(row['total_duration'] or 0) for row in agg]

    # 2️⃣ Pie: count of records by idle
    pie = (qs.values('idle')
             .annotate(count=Count('idle'))
             .order_by('-count'))
    pie_labels = [row['idle'] for row in pie]
    pie_data   = [row['count'] for row in pie]

        # 3️⃣ Dept-wise Bar: aggregate total_duration by department
    dept_agg = (qs.values('downtime_dept')
                   .annotate(total_duration=Sum('total_duration'))
                   .order_by('downtime_dept'))
    dept_labels = [row['downtime_dept'] for row in dept_agg]
    dept_data   = [float(row['total_duration'] or 0) for row in dept_agg]

        # 4️⃣ Category-wise Bar: aggregate total_duration by downtime_category
    cat_agg = (qs.values('downtime_category')
                  .annotate(total_duration=Sum('total_duration'))
                  .order_by('downtime_category'))
    category_labels = [row['downtime_category'] for row in cat_agg]
    category_data   = [float(row['total_duration'] or 0) for row in cat_agg]

    # 5️⃣ Product-wise Bar: aggregate total_duration by product_name
    product_agg = (qs.values('product_name')
                    .annotate(total_duration=Sum('total_duration'))
                    .order_by('product_name'))
    product_labels = [row['product_name'] for row in product_agg]
    product_data   = [float(row['total_duration'] or 0) for row in product_agg]

    return render(request, 'downtime/downtime_chart.html', {
        'downtime_depts': downtime_depts,
        'blocks':         blocks,
        'products':       products,
        'idle_options':   idle_options,
        'selected_dept':    selected_dept,
        'selected_block':   selected_block,
        'selected_product': selected_product,
        'selected_idle':    selected_idle,
        'period':           period,
        'start_date':       start_dt.isoformat(),
        'end_date':         end_dt.isoformat(),
        'bar_labels':       json.dumps(bar_labels),
        'bar_data':         json.dumps(bar_data),
        'pie_labels':       json.dumps(pie_labels),
        'pie_data':         json.dumps(pie_data),
        'dept_labels':      json.dumps(dept_labels),
        'dept_data':        json.dumps(dept_data),
        'category_labels':  json.dumps(category_labels),
        'category_data':    json.dumps(category_data),
        'product_labels':  json.dumps(product_labels),
        'product_data':    json.dumps(product_data),
        'user_groups':      user_groups,
        'is_superuser':     is_superuser,
    })