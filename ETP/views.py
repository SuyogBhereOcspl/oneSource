from django.shortcuts import render, redirect,get_object_or_404
from django.forms import inlineformset_factory
from django.contrib import messages
from .models import EffluentRecord, EffluentQty, GeneralEffluent
from .forms import EffluentRecordForm, EffluentQtyForm,GeneralEffluentForm
from django.db import connections
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import logging
from django.core.paginator import Paginator
from django.db.models import Sum
from datetime import datetime, timedelta,date,time
from django.db.models.functions import TruncMonth
from django.utils.dateparse import parse_date
from django.db.models import Q
import xlsxwriter
import io
from calendar import monthrange
from collections import defaultdict
import re
from .models import ProductionSchedule  # via your ReadOnlyDBRouter
from urllib.parse import urlencode





logger = logging.getLogger(__name__)


#Get FG Name
def get_products(request):
    search_term = request.GET.get('term', '').lower()

    query = """
    SELECT DISTINCT
       ITMCF.sValue AS [FG_Name]
FROM   txnhdr  AS HDR
JOIN   TXNDET  AS DET   ON DET.lId   = HDR.lId
JOIN   ITMMST  AS ITM   ON ITM.lId   = DET.lItmId          -- (kept for completeness)
JOIN   ITMTYP  (NOLOCK) AS ITP  ON ITP.lTypId = DET.lItmTyp
JOIN   ITMCF   AS ITMCF
           ON  ITMCF.lId      = DET.lItmId
          AND  ITMCF.lFieldNo = 10          -- FG name CF-field
          AND  ITMCF.lLine    = 0
WHERE  HDR.lTypId     IN (664,717,718,719,720,721)  -- required Txn types
  AND  HDR.lCompId    = 27
  AND  HDR.bDel       = 0                           -- header not deleted
  AND  DET.bDel      <> -2                          -- detail not deleted
  AND  DET.lClosed   <> -2                          -- detail not closed
  AND  DET.lItmTyp   <> 63                          -- exclude item-type 63
  AND  ITP.sName    NOT IN ('WIP FR','Intercut')    -- exclude certain item-types
  AND  HDR.dtDocDate >= '20250101'                  -- date filter (yyyymmdd)
  AND ( SELECT sValue
         FROM  txncf
        WHERE  lid    = HDR.lid
          AND  sName  = 'Product Name'
          AND  lLine  = 0
      ) <> 'MIX SOLVENT';
    """

    with connections['readonly_db'].cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    # Remove duplicates, sort with match priority
    seen = set()
    results = []
    for row in rows:
        fg_name = row[0]
        if fg_name and fg_name not in seen:
            seen.add(fg_name)
            results.append(fg_name)

    # Sort: matches with search_term earlier in string come first
    if search_term:
        results.sort(key=lambda name: name.lower().find(search_term) if search_term in name.lower() else float('inf'))

    # Return as Select2 format
    return JsonResponse({'results': [{'id': name, 'text': name} for name in results]})


# Get Stage Name -------------------------------------------------------------
def get_stage_names(request):
    """
    Returns DISTINCT Product-/Stage-names (txncf.'Product Name')
    that belong to the FG selected in the first dropdown.
    The extra joins / filters are identical to get_products().
    """
    term     = request.GET.get("term", "").lower()          # what the user typed
    fg_name  = request.GET.get("product_name", "")          # FG selected above

    sql = """
    SELECT  DISTINCT                       -- one row per stage
            (SELECT sValue
               FROM  txncf
              WHERE  lid   = HDR.lid
                AND  sName = 'Product Name'
                AND  lLine = 0)            AS [Stage_Name]
    FROM        txnhdr  AS HDR
    JOIN        txndet  AS DET   ON DET.lId    = HDR.lId
    JOIN        itmmst  AS ITM   ON ITM.lId    = DET.lItmId       -- kept
    JOIN        itmtyp  (NOLOCK) AS ITP   ON ITP.lTypId = DET.lItmTyp
    JOIN        itmcf   AS ITMCF
                   ON  ITMCF.lId      = DET.lItmId
                  AND  ITMCF.lFieldNo = 10   -- FG name custom field
                  AND  ITMCF.lLine    = 0
    WHERE       HDR.lTypId  IN (664,717,718,719,720,721)
      AND       HDR.lCompId = 27
      AND       HDR.bDel    = 0
      AND       DET.bDel   <> -2
      AND       DET.lClosed <> -2
      AND       DET.lItmTyp <> 63
      AND       ITP.sName  NOT IN ('WIP FR','Intercut')
      AND       HDR.dtDocDate >= '20250101'
      AND       ITMCF.sValue = %s                     -- FG filter
      AND      (SELECT sValue
                  FROM  txncf
                 WHERE  lid   = HDR.lid
                   AND  sName = 'Product Name'
                   AND  lLine = 0) <> 'MIX SOLVENT'
    ORDER BY    [Stage_Name];
    """

    with connections["readonly_db"].cursor() as cur:
        cur.execute(sql, [fg_name])
        stages = [row[0] for row in cur.fetchall() if row[0]]   # flatten

    # ------- deduplicate & apply search-term priority -----------------------
    unique   = list(dict.fromkeys(stages))          # preserves order, removes dupes

    if term:
        # move matches (containing the user's term) to the front
        unique.sort(
            key=lambda x: (x.lower().find(term) if term in x.lower() else float("inf"), x)
        )

    return JsonResponse(
        {"results": [{"id": s, "text": s} for s in unique]}
    )



# ---------------------------------------------------------------------------
# Get Batch-Nos ( “O/P Batch No” custom-field )
# ---------------------------------------------------------------------------
@csrf_exempt
def get_batch_nos(request):
    """Return distinct Batch-numbers for the selected FG & Stage."""
    term          = request.GET.get("term", "").lower()       # live search
    fg_name       = request.GET.get("product_name", "")       # FG selected first
    stage_name    = request.GET.get("stage_name", "")         # ’Product Name’ (=Stage)

    sql = """
    SELECT  DISTINCT
            ( SELECT sValue
                FROM  txncf
               WHERE  lid   = HDR.lid
                 AND  sName = 'Batch No'
                 AND  lLine = 0
            )  AS Batch_No
    FROM        txnhdr  AS HDR
    JOIN        txndet  AS DET   ON DET.lId    = HDR.lId
    JOIN        itmmst  AS ITM   ON ITM.lId    = DET.lItmId      -- (kept)
    JOIN        itmtyp  (NOLOCK) AS ITP   ON ITP.lTypId = DET.lItmTyp
    JOIN        itmcf   AS ITMCF
               ON  ITMCF.lId      = DET.lItmId
              AND  ITMCF.lFieldNo = 10      -- FG name CF
              AND  ITMCF.lLine    = 0
    WHERE       HDR.lTypId  IN (664,717,718,719,720,721)
      AND       HDR.lCompId = 27
      AND       HDR.bDel    = 0
      AND       DET.bDel   <> -2
      AND       DET.lClosed <> -2
      AND       DET.lItmTyp <> 63
      AND       ITP.sName  NOT IN ('WIP FR','Intercut')
      AND       HDR.dtDocDate >= '20250101'
      AND       ITMCF.sValue = %s                           -- FG filter
      AND      ( SELECT sValue
                   FROM  txncf
                  WHERE  lid   = HDR.lid
                    AND  sName = 'Product Name'
                    AND  lLine = 0 ) = %s                   -- Stage filter
      AND      ( SELECT sValue
                   FROM  txncf
                  WHERE  lid   = HDR.lid
                    AND  sName = 'Product Name'
                    AND  lLine = 0 ) <> 'MIX SOLVENT'
    ORDER BY    Batch_No;
    """

    with connections["readonly_db"].cursor() as cur:
        cur.execute(sql, [fg_name, stage_name])
        batch_list = [row[0] for row in cur.fetchall() if row[0]]

    # remove duplicates kept by DISTINCT (safety) and apply live-search priority
    seen, results = set(), []
    for b in batch_list:
        if b not in seen:
            seen.add(b)
            results.append(b)

    if term:
        results.sort(
            key=lambda x: (x.lower().find(term) if term in x.lower() else float("inf"), x)
        )

    return JsonResponse(
        {"results": [{"id": b, "text": b} for b in results]}
    )



# ---------------------------------------------------------------------------
# Voucher-number for a given FG  + Stage  + Batch-No
# ---------------------------------------------------------------------------
@csrf_exempt
def get_voucher_details_by_batch(request):
    data        = json.loads(request.body.decode("utf-8") or "{}")
    fg_name     = data.get("product_name", "")
    stage_name  = data.get("stage_name", "")
    batch_no    = data.get("batch_no",   "")

    sql = """
    SELECT TOP 1 HDR.sDocNo                                          -- voucher #
    FROM   txnhdr  AS HDR
    JOIN   txndet  AS DET   ON DET.lId    = HDR.lId
    JOIN   itmtyp  (NOLOCK) ITP ON ITP.lTypId = DET.lItmTyp
    JOIN   itmcf   AS ITMCF
           ON ITMCF.lId      = DET.lItmId
          AND ITMCF.lFieldNo = 10
          AND ITMCF.lLine    = 0
    WHERE  HDR.lTypId    IN (664,717,718,719,720,721)
      AND  HDR.lCompId   = 27
      AND  HDR.bDel      = 0
      AND  DET.bDel     <> -2
      AND  DET.lClosed  <> -2
      AND  DET.lItmTyp  <> 63
      AND  ITP.sName   NOT IN ('WIP FR','Intercut')
      AND  HDR.dtDocDate >= '20250101'
      AND  ITMCF.sValue   = %s                                   -- FG name
      AND (SELECT sValue FROM txncf WHERE lid=HDR.lid AND sName='Product Name' AND lLine=0) = %s
      AND (SELECT sValue FROM txncf WHERE lid=HDR.lid AND sName='Batch No'   AND lLine=0) = %s
      AND (SELECT sValue FROM txncf WHERE lid=HDR.lid AND sName='Product Name' AND lLine=0) <> 'MIX SOLVENT';
    """

    with connections["readonly_db"].cursor() as cur:
        cur.execute(sql, [fg_name, stage_name, batch_no])
        rec = cur.fetchone()

    if rec:
        return JsonResponse({"voucher_no": rec[0]})
    return JsonResponse({"error": "Not found"}, status=404)




@csrf_exempt
@require_POST
def get_effluent_qty_details(request):
    if request.headers.get('Content-Type') == 'application/json':
        data = json.loads(request.body)
    else:
        data = request.POST

    product_name = data.get('product_name')
    stage_name = data.get('stage_name')
    batch_no = data.get('batch_no')

    # print("🔍 Incoming Request:")
    # print(f"   ➤ Product Name: {product_name}")
    # print(f"   ➤ Stage Name:   {stage_name}")
    # print(f"   ➤ Batch No:     {batch_no}")

    if not product_name or not stage_name or not batch_no:
        # print("❌ Missing one or more required parameters.")
        return JsonResponse({
            'error': 'Missing parameters: product_name, stage_name and batch_no are required.'
        }, status=400)

    query = """
        SELECT
            bl.material_category AS category,
            bl.material_name     AS effluent_nature,
            bl.quantity          AS plan_quantity,
            bl.density           AS density
        FROM bom_headers bh
        JOIN bom_lines bl ON bh.bom_id = bl.bom_id
        WHERE bh.fg_name = %s
          AND bh.stage_name = %s
          AND bl.line_type = 'waste'
    """

    try:
        with connections['production_scheduler'].cursor() as cursor:
            cursor.execute(query, [product_name, stage_name])
            rows = cursor.fetchall()
            # print(f"✅ Query executed successfully. Rows fetched: {len(rows)}")
    except Exception as e:
        # print(f"🔥 Error during DB fetch: {str(e)}")
        return JsonResponse({'error': 'Database query failed'}, status=500)

    if not rows:
        # print("⚠️ No records found for effluent quantity.")
        return JsonResponse({'error': 'No matching production schedule lines found.'}, status=404)

    results = []
    for row in rows:
        # print(f"📦 Row: {row}")
        results.append({
            'category': row[0],
            'effluent_nature': row[1],
            'plan_quantity': row[2],
            'density':        row[3],
        })

    return JsonResponse({'data': results})





def add_effluent_record(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser
    if not request.user.has_perm('ETP.add_effluentrecord'):
        logger.warning(f"Unauthorized add attempt by {request.user.username}")
        messages.error(request, "You do not have permission to add Effluent records.")
        return redirect('indexpage')
    
    EffluentQtyFormSet = inlineformset_factory(
        EffluentRecord, EffluentQty, form=EffluentQtyForm,
        extra=1, can_delete=True )
    
    FORMSET_PREFIX = "effluentqty_set" 

    if request.method == 'POST':
        logger.debug("🔄 Received POST request")
        logger.debug(f"📦 POST Data: {request.POST.dict()}")

        record_form = EffluentRecordForm(request.POST)
        formset = EffluentQtyFormSet(request.POST, prefix=FORMSET_PREFIX)

        if record_form.is_valid():
            logger.debug("✅ Record form is valid")
        else:
            logger.error(f"❌ Record form errors: {record_form.errors.as_json()}")

        if formset.is_valid():
            logger.debug("✅ Formset is valid")
        else:
            for i, f in enumerate(formset.forms):
                if f.errors:
                    logger.error(f"  - Row {i} Errors: {f.errors.as_json()}")

        if record_form.is_valid() and formset.is_valid():
            effluent_record = record_form.save()
            formset.instance = effluent_record
            formset.save()
            logger.info("✅ Effluent record and quantities saved successfully.")
            messages.success(request, "Effluent record added successfully!")
            return redirect('view_effluent_records')
        else:
            logger.warning("⚠️ Form validation failed. Rendering form with errors.")
            messages.error(request, "Please correct the errors below.")
    else:
        record_form = EffluentRecordForm()
        formset = EffluentQtyFormSet(prefix=FORMSET_PREFIX)

    return render(request, 'etp/add_effluent_record.html', {
        'record_form': record_form,
        'formset': formset,
        'user_groups': user_groups,
        'is_superuser': is_superuser,
    })



@login_required
def effluent_records_list(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser

    if not request.user.has_perm('ETP.view_effluentrecord'):
        logger.warning(f"Unauthorized view attempt by user: {request.user.username}")
        messages.error(request, "You do not have permission to View Effluent records.")
        return redirect('indexpage')

    today = date.today()
    first_day = today.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Filters
    product_name = request.GET.get('product_name', '').strip()
    stage_name = request.GET.get('stage_name', '').strip()
    block = request.GET.get('block', '').strip()
    category = request.GET.get('category', '').strip()

    from_str = request.GET.get('from_date', '')
    to_str = request.GET.get('to_date', '')
    from_date = parse_date(from_str) if from_str else first_day
    to_date = parse_date(to_str) if to_str else last_day

    logger.info(f"User {request.user.username} filtering effluent records from {from_date} to {to_date}, "
                f"product_name='{product_name}', stage_name='{stage_name}', block='{block}', category='{category}'")

    # Query
    records = EffluentQty.objects.select_related('effluent_record') \
        .filter(effluent_record__record_date__range=(from_date, to_date)) \
        .order_by('-effluent_record__record_date', '-effluent_record__id')

    if product_name:
        records = records.filter(effluent_record__product_name__icontains=product_name)
    if stage_name:
        records = records.filter(effluent_record__stage_name__icontains=stage_name)
    if block:
        records = records.filter(effluent_record__block=block)
    if category:
        records = records.filter(category=category)

    totals = records.aggregate(
        total_plan_quantity=Sum('plan_quantity'),
        total_actual_quantity=Sum('actual_quantity'),
        total_quantity_kg=Sum('quantity_kg')
    )

    paginator = Paginator(records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    all_blocks = EffluentQty.objects.values_list('effluent_record__block', flat=True).distinct()
    all_categories = EffluentQty.objects.values_list('category', flat=True).distinct()

    filter_params = {
        'from_date': from_str or '',
        'to_date': to_str or '',
        'product_name': product_name,
        'stage_name': stage_name,
        'block': block,
        'category': category,
    }
    filter_query = urlencode({k: v for k, v in filter_params.items() if v})

    logger.debug(f"Returned {page_obj.paginator.count} effluent records, page {page_number or 1}")

    return render(request, 'etp/view_effluent_records.html', {
        'user_groups': user_groups,
        'is_superuser': is_superuser,
        'page_obj': page_obj,
        'all_blocks': all_blocks,
        'all_categories': all_categories,
        'totals': totals,
        'filters': {
            'product_name': product_name,
            'stage_name': stage_name,
            'block': block,
            'category': category,
            'from_date': from_date.strftime('%Y-%m-%d'),
            'to_date': to_date.strftime('%Y-%m-%d'),
        },
        'filter_query': filter_query,
    })


@login_required
def edit_effluent_record(request, pk):
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser
    if not request.user.has_perm('ETP.change_effluentrecord'):
        logger.warning(f"Unauthorized add attempt by {request.user.username}")
        messages.error(request, "You do not have permission to update Effluent records.")
        return redirect('indexpage')
    record = get_object_or_404(EffluentRecord, id=pk)
    EffluentQtyFormSet = inlineformset_factory(
        EffluentRecord, EffluentQty, form=EffluentQtyForm,
        extra=0, can_delete=True
    )
    FORMSET_PREFIX = "effluentqty_set"

    if request.method == 'POST':
        record_form = EffluentRecordForm(request.POST, instance=record)
        formset = EffluentQtyFormSet(request.POST, instance=record, prefix=FORMSET_PREFIX)

        if record_form.is_valid() and formset.is_valid():
            record_form.save()
            formset.save()
            messages.success(request, "Effluent record updated successfully!")
            return redirect('view_effluent_records')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        record_form = EffluentRecordForm(instance=record)
        formset = EffluentQtyFormSet(instance=record, prefix=FORMSET_PREFIX)

        # Fetch densities from BOM for each nature
        fg_name    = record.product_name
        stage_name = record.stage_name
        query = """
            SELECT material_name, density
            FROM bom_lines bl
            JOIN bom_headers bh ON bl.bom_id = bh.bom_id
            WHERE bh.fg_name = %s AND bh.stage_name = %s AND bl.line_type = 'waste'
        """
        density_map = {}
        with connections['production_scheduler'].cursor() as cursor:
            cursor.execute(query, [fg_name, stage_name])
            for mat_name, density in cursor.fetchall():
                density_map[mat_name] = density or 0

        # Inject density into each form’s initial data
        for form in formset:
            nature = form.initial.get('effluent_nature')
            form.initial['density'] = density_map.get(nature, 0)

    return render(request, 'etp/edit_effluent_record.html', {
        'user_groups': user_groups,
        'is_superuser': is_superuser,
        'record_form': record_form,
        'formset': formset,
        'record': record,
        'edit_mode': True,
    })



@login_required
def delete_effluent_qty(request, qty_id):
    if not request.user.has_perm('ETP.delete_effluentrecord'):
        logger.warning(f"Unauthorized add attempt by {request.user.username}")
        messages.error(request, "You do not have permission to delete Effluent records.")
        return redirect('indexpage')
    qty = get_object_or_404(EffluentQty, id=qty_id)

    # Check related record
    eff_record = qty.effluent_record
    sibling_count = EffluentQty.objects.filter(effluent_record=eff_record).count()

    if request.method == 'POST':
        qty.delete()
        msg = "Effluent Record deleted successfully."

        # If it was the only one, delete the parent record
        if sibling_count == 1:
            eff_record.delete()
            msg = "Effluent record deleted successfully."

        messages.success(request, msg)
        return redirect('view_effluent_records')

    messages.error(request, "Invalid request.")
    return redirect('view_effluent_records')



@login_required
def download_effluent_excel(request):
    today = datetime.today().date()
    first_day = today.replace(day=1)
    last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

    product_name = request.GET.get('product_name', '').strip()
    stage_name = request.GET.get('stage_name', '').strip()
    block = request.GET.get('block', '').strip()
    category = request.GET.get('category', '').strip()
    from_str = request.GET.get('from_date', '')
    to_str = request.GET.get('to_date', '')

    from_date = parse_date(from_str) if from_str else first_day
    to_date = parse_date(to_str) if to_str else last_day

    qs = EffluentQty.objects.select_related('effluent_record') \
        .filter(effluent_record__record_date__range=(from_date, to_date)) \
        .order_by('-effluent_record__record_date')

    if product_name:
        qs = qs.filter(effluent_record__product_name__icontains=product_name)
    if stage_name:
        qs = qs.filter(effluent_record__stage_name__icontains=stage_name)
    if block:
        qs = qs.filter(effluent_record__block=block)
    if category:
        qs = qs.filter(category=category)

    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {'in_memory': True})
    ws = wb.add_worksheet("Effluent Records")

    header_fmt = wb.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1, 'align': 'center'})
    date_fmt = wb.add_format({'num_format': 'dd/mm/yyyy', 'align': 'center'})
    text_fmt = wb.add_format({'align': 'left'})
    num_fmt = wb.add_format({'num_format': '#,##0.00', 'align': 'right'})

    headers = [
        "Sr. No", "Record Date", "Product Name", "Stage Name", "Category",
        "Block", "Effluent Nature", "Plan Quantity (Kg)", "Actual Quantity (Kl)", "Quantity (Kg)"
    ]
    for col, header in enumerate(headers):
        ws.write(0, col, header, header_fmt)

    ws.set_column('A:A', 8)
    ws.set_column('B:B', 12)
    ws.set_column('C:C', 25)
    ws.set_column('D:D', 25)
    ws.set_column('E:E', 12)
    ws.set_column('F:F', 12)
    ws.set_column('G:G', 25)
    ws.set_column('H:J', 18)

    row = 1
    for idx, rec in enumerate(qs, start=1):
        eff = rec.effluent_record
        ws.write_number(row, 0, idx)
        ws.write_datetime(row, 1, datetime.combine(eff.record_date, time()), date_fmt)
        ws.write_string(row, 2, eff.product_name or '', text_fmt)
        ws.write_string(row, 3, eff.stage_name or '', text_fmt)
        ws.write_string(row, 4, rec.category or '', text_fmt)
        ws.write_string(row, 5, eff.block or '', text_fmt)
        ws.write_string(row, 6, rec.effluent_nature or '', text_fmt)
        ws.write_number(row, 7, rec.plan_quantity or 0.0, num_fmt)
        ws.write_number(row, 8, rec.actual_quantity or 0.0, num_fmt)
        ws.write_number(row, 9, rec.quantity_kg or 0.0, num_fmt)
        row += 1

    wb.close()
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="effluent_records.xlsx"'
    return response


def parse_batch_count(s):
    try:
        inside = s.split('(')[1].split(')')[0]  # "34 / 5,273"
        batch_count = inside.split('/')[0].strip()
        return int(batch_count.replace(',', ''))
    except Exception:
        return 0


def generate_batch_rows(schedule):
    """
    Produce one dict per batch with:
      - batch_no, generated_batch_number
      - batch_start, batch_end
      - output_quantity
      - equipment_runs: list of {
            equipment_id, std_bct, wait_time, star, start, end, status
        }
      - materials, outputs, wastes: full lists of schedule lines

    Runs whose start >= their closed_date or the schedule’s closed_date
    are marked "Cancelled" (but still emitted in the CSV).
    """
    from datetime import datetime as _dt, timedelta as _td

    # ─── 0) Determine plan-level cutoff if any ─────────────────────────
    plan_cutoff = getattr(schedule, "closed_date", None)
    if plan_cutoff and not isinstance(plan_cutoff, _dt):
        plan_cutoff = _dt.combine(plan_cutoff, _dt.min.time())

    # ─── 1) Basic header values ───────────────────────────────────────
    n_batches = int(schedule.no_of_batches or 0)
    approach  = int(schedule.scheduling_approach or 0)
    start_ts  = schedule.start_date
    if not isinstance(start_ts, _dt):
        start_ts = _dt.combine(start_ts, _dt.min.time())

    # ─── 2) Per-batch output ──────────────────────────────────────────
    lines = schedule.lines.all()
    out_ln = next((l for l in lines if l.line_type == "output"), None)
    per_batch = round(float(out_ln.quantity or 0)) if out_ln else 0

    # ─── 3) Pull materials/outputs/wastes once ────────────────────────
    mats = [
        dict(
            line_type="input",
            material_category=l.material_category,
            material_name=l.material_name,
            quantity=l.quantity,
            ratio=l.ratio,
            density=l.density,
            litre=l.litre,
            include_in_total=l.include_in_total
        )
        for l in lines if l.line_type == "input"
    ]
    outs = [
        dict(
            line_type="output",
            material_category=l.material_category,
            material_name=l.material_name,
            quantity=l.quantity,
            ratio=l.ratio,
            density=l.density,
            litre=l.litre
        )
        for l in lines if l.line_type == "output"
    ]
    wsts = [
        dict(
            line_type="waste",
            material_category=l.material_category,
            material_name=l.material_name,
            quantity=l.quantity,
            ratio=l.ratio,
            density=l.density,
            litre=l.litre
        )
        for l in lines if l.line_type == "waste"
    ]

    # ─── 4) Build equipment state ─────────────────────────────────────
    eq_lines = [l for l in lines if l.line_type == "equipment"]
    if not eq_lines or n_batches < 1:
        return []

    eq_state = []
    for l in eq_lines:
        eq_state.append({
            "equipment_id": l.equipment_id,
            "std":          float(l.std_bct or 0),
            "wait":         float(l.wait_time or 0),
            "next":         start_ts,
            "star":         bool(getattr(l, "star", False)),
            "closed_date":  l.closed_date
        })

    # ─── helper to build generated_batch_number ───────────────────────
    def gen_num(i):
        base = schedule.batch_number or ""
        if len(base) >= 2 and base[-2:].isdigit():
            prefix, start = base[:-2], int(base[-2:])
            return prefix + str(start + i).zfill(2)
        return str(i).zfill(2)

    batches = []

    # ─── FIFO ─────────────────────────────────────────────────────────
    if approach == 1:
        for i in range(1, n_batches + 1):
            cell = min(eq_state, key=lambda x: x["next"])
            st   = cell["next"]
            et   = st + _td(hours=cell["std"])

            is_cancel = False
            if cell["closed_date"] and st >= cell["closed_date"]:
                is_cancel = True
            if plan_cutoff and st >= plan_cutoff:
                is_cancel = True
            status = "Cancelled" if is_cancel else "Scheduled"

            if status == "Scheduled":
                cell["next"] = et + _td(hours=cell["wait"])

            runs = [{
                "equipment_id": cell["equipment_id"],
                "std_bct":      cell["std"],
                "wait_time":    cell["wait"],
                "star":         cell["star"],
                "start":        st,
                "end":          et,
                "status":       status
            }]

            batches.append({
                "batch_no":               i,
                "generated_batch_number": gen_num(i),
                "batch_start":            st,
                "batch_end":              et,
                "output_quantity":        per_batch,
                "equipment_runs":         runs,
                "materials":              mats,
                "outputs":                outs,
                "wastes":                 wsts,
            })

    # ─── ROLL ─────────────────────────────────────────────────────────
    elif approach == 0:
        pipeline = [dict(e) for e in eq_state]
        for i in range(1, n_batches + 1):
            runs = []
            prev = None
            for cell in pipeline:
                st = prev if prev and prev > cell["next"] else cell["next"]
                et = st + _td(hours=cell["std"])

                is_cancel = False
                if cell["closed_date"] and st >= cell["closed_date"]:
                    is_cancel = True
                if plan_cutoff and st >= plan_cutoff:
                    is_cancel = True
                status = "Cancelled" if is_cancel else "Scheduled"

                if status == "Scheduled":
                    cell["next"] = et + _td(hours=cell["wait"])
                    prev = cell["next"]

                runs.append({
                    "equipment_id": cell["equipment_id"],
                    "std_bct":      cell["std"],
                    "wait_time":    cell["wait"],
                    "star":         cell["star"],
                    "start":        st,
                    "end":          et,
                    "status":       status
                })

            batches.append({
                "batch_no":               i,
                "generated_batch_number": gen_num(i),
                "batch_start":            runs[0]["start"],
                "batch_end":              runs[-1]["end"],
                "output_quantity":        per_batch,
                "equipment_runs":         runs,
                "materials":              mats,
                "outputs":                outs,
                "wastes":                 wsts,
            })

    # ─── STAR ─────────────────────────────────────────────────────────
    elif approach == 3:
        stars = [e for e in eq_state if e["star"]][:2]
        if len(stars) < 2:
            need = 2 - len(stars)
            for e in eq_state:
                if not e["star"] and need:
                    e["star"] = True
                    stars.append(e)
                    need -= 1
        A, B = stars[0], stars[1]
        B["next"] = start_ts + _td(hours=B["std"] / 2)

        for i in range(1, n_batches + 1):
            omit = B if (i & 1) else A
            seq  = [e for e in eq_state if e is not omit]
            runs, prev = [], None

            for cell in seq:
                st = prev if prev and prev > cell["next"] else cell["next"]
                et = st + _td(hours=cell["std"])

                is_cancel = False
                if cell["closed_date"] and st >= cell["closed_date"]:
                    is_cancel = True
                if plan_cutoff and st >= plan_cutoff:
                    is_cancel = True
                status = "Cancelled" if is_cancel else "Scheduled"

                if status == "Scheduled":
                    cell["next"] = et + _td(hours=cell["wait"])
                    prev = cell["next"]

                runs.append({
                    "equipment_id": cell["equipment_id"],
                    "std_bct":      cell["std"],
                    "wait_time":    cell["wait"],
                    "star":         cell["star"],
                    "start":        st,
                    "end":          et,
                    "status":       status
                })

            batches.append({
                "batch_no":               i,
                "generated_batch_number": gen_num(i),
                "batch_start":            runs[0]["start"],
                "batch_end":              runs[-1]["end"],
                "output_quantity":        per_batch,
                "equipment_runs":         runs,
                "materials":              mats,
                "outputs":                outs,
                "wastes":                 wsts,
            })

    # ─── fallback ─ treat unknown as ROLL ─────────────────────────────
    else:
        schedule.scheduling_approach = 0
        return generate_batch_rows(schedule)

    return batches


def indian_number_format(num):
    try:
        num = float(num)
    except:
        return num
    s = f"{num:.2f}"
    if "." in s:
        whole, dec = s.split(".")
    else:
        whole, dec = s, ""
    if len(whole) > 3:
        last3 = whole[-3:]
        other = whole[:-3]
        other = __import__("re").sub(r"(\d)(?=(\d\d)+$)", r"\1,", other)
        whole = other + "," + last3
    return whole if dec == "00" else whole + "." + dec


def safe_round(val):
    try:
        return round(float(val))
    except:
        return val




@login_required
def effluent_plan_actual_report(request):
    user_groups = request.user.groups.values_list('name', flat=True)  # Check if the user is in STORE group
    is_superuser = request.user.is_superuser
    # 1) parse filters & dates
    today = date.today()
    year, last_mon = today.year, today.month

    fg_filter = request.GET.get("fg_name", "").strip()
    period    = request.GET.get("period", "monthly").strip().lower()
    from_str  = request.GET.get("from_date", "").strip()
    to_str    = request.GET.get("to_date", "").strip()

    def parse_date(s):
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except:
            return None

    # 2) build buckets & bucket_for
    if period == "daily":
        start = parse_date(from_str) or today.replace(day=1)
        end   = parse_date(to_str)   or today
        buckets = [start + timedelta(days=i) for i in range((end - start).days + 1)]
        bucket_label_items = [(d, d.strftime("%d-%b")) for d in buckets]
        bucket_for = lambda d: d

    elif period == "weekly":
        start = date(year,1,1)
        end   = date(year,last_mon, monthrange(year,last_mon)[1])
        buckets, labels = [], {}
        d = start - timedelta(days=start.weekday())
        while d <= end:
            buckets.append(d)
            labels[d] = f"W{d.isocalendar()[1]} ({d.strftime('%d-%b')})"
            d += timedelta(days=7)
        bucket_label_items = [(b, labels[b]) for b in buckets]
        bucket_for = lambda d: d - timedelta(days=d.weekday())

    elif period == "fortnightly":
        start = date(year,1,1)
        end   = date(year,last_mon, monthrange(year,last_mon)[1])
        buckets, labels = [], {}
        d = start.replace(day=1)
        while d <= end:
            buckets.append(d)
            labels[d] = f"{d.strftime('%b')} 1-15"
            d2 = d.replace(day=16)
            buckets.append(d2)
            labels[d2] = f"{d2.strftime('%b')} 16-{monthrange(d.year,d.month)[1]}"
            d = d.replace(month=d.month+1 if d.month<12 else 1,
                          year=d.year   if d.month<12 else d.year+1)
        bucket_label_items = [(b, labels[b]) for b in buckets]
        bucket_for = lambda d: d.replace(day=1) if d.day<=15 else d.replace(day=16)

    else:  # monthly
        start = date(year,1,1)
        end   = date(year,last_mon, monthrange(year,last_mon)[1])
        buckets, labels = [], {}
        d = start.replace(day=1)
        while d <= end:
            buckets.append(d.month)
            labels[d.month] = d.strftime('%b')
            d = d.replace(month=d.month+1 if d.month<12 else 1,
                          year=d.year   if d.month<12 else d.year+1)
        bucket_label_items = [(m, labels[m]) for m in buckets]
        bucket_for = lambda d: d.month

    # 3) aggregate actuals
    actual_qs = EffluentQty.objects.select_related("effluent_record")\
        .filter(effluent_record__record_date__range=(start, end))
    if fg_filter:
        actual_qs = actual_qs.filter(effluent_record__product_name=fg_filter)

    report_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
        "plan": 0.0, "actual": 0.0, "batches": set()
    })))
    for qty in actual_qs:
        rec = qty.effluent_record
        b   = bucket_for(rec.record_date)
        if b not in buckets: continue
        report_data[rec.product_name][rec.stage_name][b]["actual"] += qty.quantity_kg
        if rec.batch_no:
            report_data[rec.product_name][rec.stage_name][b]["batches"].add(rec.batch_no)

    # 4) aggregate planned
    sched_qs = ProductionSchedule.objects.using("production_scheduler")\
        .filter(start_date__date__lte=end, end_date__date__gte=start)
    if fg_filter:
        sched_qs = sched_qs.filter(product_id=fg_filter)

    planned_qty   = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    planned_count = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for sch in sched_qs:
        for batch in generate_batch_rows(sch):
            if not any(run["status"]=="Scheduled" for run in batch["equipment_runs"]):
                continue
            bkey = bucket_for(batch["batch_end"].date())
            if bkey not in buckets: continue
            for w in batch["wastes"]:
                planned_qty[sch.product_id][sch.stage_name][bkey] += w["quantity"]
            planned_count[sch.product_id][sch.stage_name][bkey] += 1

    for fg, stages in planned_qty.items():
        for stg, bm in stages.items():
            for b, val in bm.items():
                report_data[fg][stg][b]["plan"] = val
                report_data[fg][stg][b]["planned_batches"] = planned_count[fg][stg][b]

    def fmt_cell(value, batches):
        v = safe_round(value)
        s = indian_number_format(v)
        if batches:
            avg = safe_round(value / batches)
            s = f"{s} ({batches} / {indian_number_format(avg)})"
        return s

    fg_rows = []
    grand_plan = defaultdict(float)
    grand_act  = defaultdict(float)
    grand_batches = defaultdict(int)

    for fg, stages in report_data.items():
        fg_plan_total = fg_act_total = 0
        fg_plan_vals = []
        fg_act_vals  = []
        fg_plan_counts = []
        fg_act_counts = []

        for b in buckets:
            tp = sum(stages[s][b]["plan"]   for s in stages if b in stages[s])
            ta = sum(stages[s][b]["actual"] for s in stages if b in stages[s])
            pb = sum(stages[s][b].get("planned_batches",0) for s in stages if b in stages[s])
            ab = len(set().union(*(stages[s][b]["batches"] for s in stages if b in stages[s])))

            fg_plan_counts.append(pb)
            fg_act_counts.append(ab)
            fg_plan_total += tp
            fg_act_total  += ta
            grand_plan[b] += tp
            grand_act[b] += ta
            grand_batches[b] |= ab

            fg_plan_vals.append({
                "display": fmt_cell(tp, pb),
                "batch_count": pb,
            })
            fg_act_vals.append({
                "display": fmt_cell(ta, ab),
                "batch_count": ab,
            })

        fg_total_plan_s = fmt_cell(fg_plan_total, sum(fg_plan_counts))
        fg_total_act_s  = fmt_cell(fg_act_total,  sum(fg_act_counts))

        stages_list = []
        for stg, bm in stages.items():
            st_plan_vals = []
            st_act_vals  = []
            st_plan_counts = []
            st_act_counts = []

            for b in buckets:
                p = bm[b]["plan"] if b in bm else 0
                a = bm[b]["actual"] if b in bm else 0
                pb = bm[b].get("planned_batches",0)
                ab = len(bm[b]["batches"]) if b in bm else 0

                st_plan_counts.append(pb)
                st_act_counts.append(ab)
                st_plan_vals.append({
                    "display": fmt_cell(p, pb),
                    "batch_count": pb,
                })
                st_act_vals.append({
                    "display": fmt_cell(a, ab),
                    "batch_count": ab,
                })

            stage_total_plan_s = fmt_cell(sum(p["batch_count"] for p in st_plan_vals), sum(st_plan_counts))
            stage_total_act_s  = fmt_cell(sum(a["batch_count"] for a in st_act_vals),  sum(st_act_counts))

            stages_list.append({
                "stage": stg,
                "month_pairs": list(zip(st_plan_vals, st_act_vals)),
                "total_plan": stage_total_plan_s,
                "total_act" : stage_total_act_s,
            })

        fg_rows.append({
            "fg": fg,
            "month_pairs": list(zip(fg_plan_vals, fg_act_vals)),
            "total_plan": fg_total_plan_s,
            "total_act": fg_total_act_s,
            "stages": stages_list,
        })

    grand_pairs = []
    grand_tp = sum(grand_plan.values())
    grand_ta = sum(grand_act.values())
    grand_pb = sum(planned_count[fg][stg][b] 
                   for fg in report_data for stg in report_data[fg] for b in buckets)
    grand_ab = sum(grand_batches[b] for b in buckets)

    grand_total_plan_s = fmt_cell(grand_tp, grand_pb)
    grand_total_act_s  = fmt_cell(grand_ta, grand_ab)

    grand_month_pairs = [
        [fmt_cell(grand_plan[b], sum(planned_count[fg][stg][b] for fg in report_data for stg in report_data[fg])),
         fmt_cell(grand_act[b],  grand_batches[b])]
        for b in buckets
    ]

    grand_totals = {
        "month_pairs": grand_month_pairs,
        "total_plan":  grand_total_plan_s,
        "total_act":   grand_total_act_s,
    }

    return render(request, "etp/effluent_report_plan_actual.html", {
        "fg_list":             EffluentRecord.objects.values_list("product_name", flat=True).distinct(),
        "fg_filter":           fg_filter,
        "period":              period,
        "from_date":           from_str if period=="daily" else "",
        "to_date":             to_str   if period=="daily" else "",
        "bucket_label_items":  bucket_label_items,
        "fg_rows":             fg_rows,
        "grand_totals":        grand_totals,
        'user_groups':         user_groups,
        'is_superuser':        is_superuser,
    })









#---------------------------------------------------------------------------------------------------------------------
#####  Below is the general effluent #####################





@login_required
def add_general_effluent(request):
    user_groups = request.user.groups.values_list('name', flat=True)  # Check if the user is in STORE group
    is_superuser = request.user.is_superuser
    # ✅ Add Permission Check
    if not request.user.has_perm('ETP.add_generaleffluent'):
        logger.warning(f"Unauthorized add attempt by {request.user.username}")
        messages.error(request, "You do not have permission to add General Effluent records.")
        return redirect('indexpage')
    
    if request.method == 'POST':
        form = GeneralEffluentForm(request.POST)
        if form.is_valid():
            instance = form.save()
            logger.info(f"GeneralEffluent record added by {request.user.username}: ID {instance.id}")
            messages.success(request, "Effluent record added successfully.")
            return redirect('view_general_effluent')  # Or redirect to another page
        else:
            messages.error(request, "Please correct the errors below.")
            logger.warning(f"Invalid form submitted by {request.user.username}: {form.errors}")
    else:
        form = GeneralEffluentForm()

    return render(request, 'etp/add_general_effluent.html', {
        'form': form,
        'user_groups': user_groups,
        'is_superuser': is_superuser
    })



@login_required
def view_general_effluent_records(request):
    user_groups  = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser 

    if not request.user.has_perm('ETP.view_generaleffluent'):
        logger.warning(f"Unauthorized view attempt by {request.user.username}")
        messages.error(request, "You do not have permission to view General Effluent records.")
        return redirect('indexpage')

    # 🔍 Read filters
    selected_location    = request.GET.get('location', '')
    selected_nature      = request.GET.get('effluent_nature', '')
    selected_period      = request.GET.get('period', 'Monthly')
    start_str            = request.GET.get('start_date', '')
    end_str              = request.GET.get('end_date', '')

    # 📄 Base queryset (most recent first)
    qs = GeneralEffluent.objects.all().order_by('-record_date')

    # 📅 Apply period filter
    today = date.today()
    if selected_period == 'Weekly':
        start_dt = today - timedelta(days=7)
        end_dt   = today
    elif selected_period == 'Custom':
        try:
            start_dt = datetime.strptime(start_str, '%Y-%m-%d').date()
        except ValueError:
            start_dt = today.replace(day=1)
        try:
            end_dt = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            end_dt = today
    else:  # Monthly
        start_dt = today.replace(day=1)
        end_dt   = today

    qs = qs.filter(record_date__gte=start_dt, record_date__lte=end_dt)

    # 🔍 Apply location & nature filters
    if selected_location:
        qs = qs.filter(location=selected_location)
    if selected_nature:
        qs = qs.filter(effluent_nature=selected_nature)

    # ➕ total quantity
    total_quantity = qs.aggregate(total=Sum('actual_quantity'))['total'] or 0.0

    # 🔄 distinct filter options
    locations         = GeneralEffluent.objects.values_list('location', flat=True).distinct().order_by('location')
    effluent_natures  = GeneralEffluent.objects.values_list('effluent_nature', flat=True).distinct().order_by('effluent_nature')

    # 📑 pagination
    paginator   = Paginator(qs, 10)
    page_number = request.GET.get('page')
    page_obj    = paginator.get_page(page_number)

    return render(request, 'etp/view_general_effluent.html', {
        'page_obj':          page_obj,
        'user_groups':       user_groups,
        'is_superuser':      is_superuser,
        'locations':         locations,
        'effluent_natures':  effluent_natures,
        'total_quantity':    total_quantity,
        # pass filter state back to template
        'selected_location':   selected_location,
        'selected_nature':     selected_nature,
        'selected_period':     selected_period,
        'start_date':          start_dt.isoformat(),
        'end_date':            end_dt.isoformat(),
    })



@login_required
def edit_general_effluent(request, pk):
    instance = get_object_or_404(GeneralEffluent, pk=pk)
    """ Edit a GeneralEffluent entry (Permission Required: ETP.change_generaleffluent) """
    if not request.user.has_perm('ETP.change_generaleffluent'):
        logger.warning(f"Unauthorized edit attempt by {request.user.username} on effluent ID {pk}")
        messages.error(request, "You do not have permission to edit General Effluent records.")
        return redirect('indexpage')
    user_groups = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser

    if request.method == 'POST':
        form = GeneralEffluentForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            logger.info(f"GeneralEffluent record updated by {request.user.username}: ID {instance.id}")
            messages.success(request, "Effluent record updated successfully.")
            return redirect('view_general_effluent')  # or wherever you want
        else:
            messages.error(request, "Please correct the errors below.")
            logger.warning(f"Invalid edit form by {request.user.username}: {form.errors}")
    else:
        form = GeneralEffluentForm(instance=instance)

    return render(request, 'etp/edit_general_effluent.html', {
        'form': form,
        'user_groups': user_groups,
        'is_superuser': is_superuser,
        'instance': instance
    })



@login_required
def delete_general_effluent(request, pk):
    record = get_object_or_404(GeneralEffluent, pk=pk)  
    """ Delete a GeneralEffluent entry (Permission Required: ETP.delete_generaleffluent) """
    if not request.user.has_perm('ETP.delete_generaleffluent'):
        logger.warning(f"Unauthorized delete attempt by {request.user.username} on effluent ID {record.id}")
        messages.error(request, "You do not have permission to delete General Effluent records.")
        return redirect('indexpage')

    if request.method == 'POST':
        record.delete()
        messages.success(request, "General Effluent record deleted successfully.")
        return redirect('view_general_effluent')

    messages.error(request, "Invalid request.")
    return redirect('view_general_effluent')


@login_required
def general_effluent_charts(request):
    user_groups  = request.user.groups.values_list('name', flat=True)
    is_superuser = request.user.is_superuser

    # 1) Pull filter params (defaults: period="mtd", no location/nature)
    period         = request.GET.get('period', 'mtd')
    from_date_str  = request.GET.get('from_date', '')
    to_date_str    = request.GET.get('to_date', '')
    location_filt  = request.GET.get('location', '').strip()
    nature_filt    = request.GET.get('effluent_nature', '').strip()

    # 2) Build base queryset and apply date range
    qs = GeneralEffluent.objects.all()
    today = date.today()

    if period == 'weekly':
        start_date = today - timedelta(days=7)
        end_date   = today
    elif period == 'fortnightly':
        start_date = today - timedelta(days=15)
        end_date   = today
    elif period == 'custom' and from_date_str and to_date_str:
        # parse_date returns a date or None
        d1 = parse_date(from_date_str)
        d2 = parse_date(to_date_str)
        if d1 and d2:
            start_date, end_date = d1, d2
        else:
            # fallback to MTD if parse fails
            start_date = today.replace(day=1)
            end_date   = today
    else:  # "mtd" or any invalid
        start_date = today.replace(day=1)
        end_date   = today

    qs = qs.filter(record_date__gte=start_date, record_date__lte=end_date)

    # 3) Optional location / nature filters
    if location_filt:
        qs = qs.filter(location=location_filt)
    if nature_filt:
        qs = qs.filter(effluent_nature=nature_filt)

    # 4) Aggregate for charts
    loc_agg = (
        qs.values('location')
          .annotate(total=Sum('actual_quantity'))
          .order_by('location')
    )
    loc_labels = [row['location'] or 'Unknown' for row in loc_agg]
    loc_data   = [row['total'] for row in loc_agg]

    nature_agg = (
        qs.values('effluent_nature')
          .annotate(total=Sum('actual_quantity'))
          .order_by('effluent_nature')
    )
    nature_labels = [row['effluent_nature'] or 'Unknown' for row in nature_agg]
    nature_data   = [row['total'] for row in nature_agg]
    # in your view, before render(...)
    ALL_LOCATIONS = (
        GeneralEffluent.objects
        .values_list("location", flat=True)
        .distinct()
        .order_by("location")
    )
    ALL_NATURES = (
        GeneralEffluent.objects
        .values_list("effluent_nature", flat=True)
        .distinct()
        .order_by("effluent_nature")
    )
    # 5) Render, passing back filter state
    return render(request, 'etp/general_effluent_charts.html', {
        'loc_labels':        json.dumps(loc_labels),
        'loc_data':          json.dumps(loc_data),
        'nature_labels':     json.dumps(nature_labels),
        'nature_data':       json.dumps(nature_data),
        'user_groups':       user_groups,
        'is_superuser':      is_superuser,

        # pass these so your template can pre-fill the form controls:
        'period':            period,
        'from_date':         from_date_str,
        'to_date':           to_date_str,
        'location_filter':   location_filt,
        'nature_filter':     nature_filt,
        "ALL_LOCATIONS": ALL_LOCATIONS,
        "ALL_NATURES": ALL_NATURES,
    })


