import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import openpyxl
from pprint import pprint
import pandas as pd
from .models import *
from .forms import *
from django.http import HttpResponse, Http404, JsonResponse
from django.db import connections, transaction
from django.db.models import Prefetch, Count, DateField, Q
from django.views.decorators.http import require_GET
from django.utils.timezone import localtime
from django.utils import timezone
from datetime import date
from django.core.mail import send_mail
from django.conf import settings
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.db.models import Func
import itertools, csv
from django.db.models import Prefetch
from datetime import datetime
from django.core.management import call_command
from io import StringIO
# ReportLab Platypus imports
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from django.core.mail import EmailMessage
from io import BytesIO





# Initialize custom logger
logger = logging.getLogger('custom_logger')


# Create your views here.

def _get_stages_from_bom():
    """
    Returns a list of dicts, one per unique item_name in LocalBOMDetail:
      [
        {
          "item_name":  "<StageName>",
          "fg_name":    "<FGName>",
          "bom_code":   "<BOMCode>",
          "itm_type":   "<ItemTypeFromERP>",
        },
        ...
      ]
    """
    # 1) Grab unique stage names (just the name column)
    names = (
        LocalBOMDetail.objects
        .values_list('item_name', flat=True)
        .distinct()
        .order_by('item_name')
    )

    stages = []
    for name in names:
        # 2) pick the first matching row for this name
        detail = LocalBOMDetail.objects.filter(item_name=name).first()
        if not detail:
            continue
        stages.append({
            "item_name": detail.item_name,
            "fg_name":   detail.fg_name,
            "bom_code":  detail.bom_code,
            "itm_type":  detail.itm_type,
        })

    return stages

@login_required
def product_list(request):
    """
    Display a list of all products, prefetched with their related specs.
    We attach `.visible_specs` to each product, filtering out any blank-named specs.
    """
    products = Product.objects.prefetch_related('specs').all()
    for p in products:
        p.visible_specs = [s for s in p.specs.all() if s.name and s.name.strip()]
    return render(request, 'products/product_list.html', {
        'products': products
    })


@login_required
def product_detail(request, pk):
    """
    Show a read-only detail page for one Product.
    """
    product = get_object_or_404(Product, pk=pk)
    # reuse the same visible_specs logic you had in list:
    visible_specs = [s for s in product.specs.all() if s.name and s.name.strip()]

    return render(request, 'products/product_detail.html', {
        'product':       product,
        'visible_specs': visible_specs,
    })




@login_required
def product_create(request):
    appearance_options = list(
        AppearanceOption.objects.values_list("name", flat=True).order_by("name")
    )
    stages = _get_stages_from_bom()

    if request.method == "POST":
        form = ProductForm(request.POST)
        temp_product = Product()
        formset = SpecFormSetCreate(request.POST, instance=temp_product)

        if form.is_valid() and formset.is_valid():
            product = form.save()
            formset.instance = product
            formset.save()
            messages.success(request, f"Product '{product.name}' created successfully.")
            logger.info(f"Product '{product.name}' created by {request.user.username}.")
            return redirect("product_list")
        else:
            messages.error(
                request,
                "There was an error creating the product. Please correct the errors below."
            )
            logger.warning(f"Product creation failed by {request.user.username}. Errors: {form.errors}, Formset errors: {formset.errors}")
    else:
        form = ProductForm()
        formset = SpecFormSetCreate(instance=Product())

    return render(request, "products/product_form.html", {
        "form":               form,
        "formset":            formset,
        "action":             "Create",
        "appearance_options": appearance_options,
        "stages":             stages,
    })



@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)

    appearance_options = list(
        AppearanceOption.objects.values_list("name", flat=True).order_by("name")
    )
    stages = _get_stages_from_bom()

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        formset = SpecFormSetUpdate(request.POST, instance=product)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f"Product '{product.name}' updated successfully.")
            logger.info(f"Product '{product.name}' updated by {request.user.username}.")
            return redirect("product_list")
        else:
            logger.warning(f"Product update failed for '{product.name}' by {request.user.username}. Form errors: {form.errors}, Formset errors: {formset.errors}")
            print("\n[DEBUG] ProductForm Errors:")
            pprint(form.errors)
            print("\n[DEBUG] SpecFormSet Errors:")
            for f in formset:
                pprint(f.errors)
            print("\n[DEBUG] Formset Non-form Errors:")
            pprint(formset.non_form_errors())
            messages.error(
                request,
                "There was an error updating the product. Please correct the errors below."
            )
    else:
        form = ProductForm(instance=product)
        formset = SpecFormSetUpdate(instance=product)

    return render(request, "products/product_form.html", {
        "form":               form,
        "formset":            formset,
        "action":             "Update",
        "appearance_options": appearance_options,
        "stages":             stages,
    })



@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        logger.info(f"Product '{product.name}' deleted by {request.user.username}.")
        product.delete()
        messages.success(request, f"Product '{product.name}' deleted.")
        return redirect('product_list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})



@login_required
def home(request):
    """
    A simple home view: renders templates/home.html
    """
    return render(request, 'home.html')


@login_required
def import_appearance_view(request):
    if request.method == "POST":
        form = ImportAppearanceForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = form.cleaned_data['file']
            try:
                wb = openpyxl.load_workbook(excel_file)
            except Exception as e:
                logger.error(f"Could not open the uploaded appearance file: {e}")
                messages.error(request, f"Could not open the uploaded file: {e}")
                return render(request, "products/import_appearance.html", {'form': form})

            sheet = wb.active
            imported_count = skipped_count = 0

            for row in sheet.iter_rows(min_row=2, values_only=True):
                raw_name = row[0]
                if not raw_name:
                    continue
                name = str(raw_name).strip()
                if not name:
                    continue

                obj, created = AppearanceOption.objects.get_or_create(name=name)
                if created:
                    imported_count += 1
                else:
                    skipped_count += 1

            messages.success(
                request,
                f"Import complete: {imported_count} new option(s) added, {skipped_count} skipped."
            )
            logger.info(f"Appearance import by {request.user.username}: {imported_count} added, {skipped_count} skipped.")
            return redirect("import_appearance")
    else:
        form = ImportAppearanceForm()

    return render(request, "products/import_appearance.html", {'form': form})


@login_required
def import_specs(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = SpecUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['excel_file']
            try:
                df = pd.read_excel(file)
            except Exception as e:
                logger.error(f"Spec Excel import failed for product {product.name}: {e}")
                messages.error(request, f"Could not read Excel: {e}")
                return redirect('spec_upload', pk=pk)

            required = {'Name', 'Type', 'Choices', 'Min Value', 'Max Value'}
            missing = required - set(df.columns)
            if missing:
                logger.warning(f"Spec import missing columns: {missing} (User: {request.user.username})")
                messages.error(request, f"Missing columns: {', '.join(missing)}")
                return redirect('spec_upload', pk=pk)

            created = updated = 0
            for _, row in df.iterrows():
                name      = str(row['Name']).strip()
                spec_type = str(row['Type']).strip().lower()
                choices   = str(row['Choices']).strip() or ''
                minv      = row['Min Value']
                maxv      = row['Max Value']

                defaults = {
                    'spec_type':      spec_type,
                    'allowed_choices': choices,
                    'min_val':        minv if pd.notna(minv) else None,
                    'max_val':        maxv if pd.notna(maxv) else None,
                }
                spec, created_flag = Spec.objects.update_or_create(
                    product=product,
                    name=name,
                    defaults=defaults
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1

            messages.success(
                request,
                f"Import complete: {created} created, {updated} updated."
            )
            logger.info(f"Specs imported for '{product.name}' by {request.user.username}: {created} created, {updated} updated.")
            return redirect('product_update', pk=pk)

    else:
        form = SpecUploadForm()

    return render(request, 'products/spec_upload.html', {
        'product': product,
        'form':     form,
    })






def is_qc_user(u):
    return u.groups.filter(name="QC").exists()


class TruncFortnight(Func):
    function = 'DATEADD'
    template = """
      DATEADD(
        day,
        -(
          DATEDIFF(day, '1900-01-01', %(expressions)s) %%%% 14
        ),
        %(expressions)s
      )
    """
    output_field = DateField()

@login_required
def dashboard(request):
    status_counts   = QCEntry.objects.order_by().values('status').annotate(count=Count('pk'))
    decision_counts = QCEntry.objects.order_by().values('decision_status').annotate(count=Count('pk'))
    stats = {
        'total':     QCEntry.objects.count(),
        'draft':     next((c['count'] for c in status_counts if c['status']=='draft'), 0),
        'pending':   next((c['count'] for c in status_counts if c['status']=='pending_qc'), 0),
        'completed': next((c['count'] for c in status_counts if c['status']=='qc_completed'), 0),
        'cancelled': next((c['count'] for c in status_counts if c['status']=='cancelled'), 0),
        'approved':  next((c['count'] for c in decision_counts if c['decision_status']=='approved'), 0),
        'variation': next((c['count'] for c in decision_counts if c['decision_status']=='approved_under_deviation'), 0),
        'rejected':  next((c['count'] for c in decision_counts if c['decision_status']=='rejected'), 0),
    }

    freq = request.GET.get('freq', 'daily')
    if freq == 'weekly':
        trunc = TruncWeek('entry_date')
    elif freq == 'monthly':
        trunc = TruncMonth('entry_date')
    elif freq == 'fortnightly':
        trunc = TruncFortnight('entry_date')
    else:
        trunc = TruncDay('entry_date')

    period_data = (
        QCEntry.objects
        .annotate(period=trunc)
        .values('period')
        .annotate(count=Count('pk'))
        .order_by('period')
    )
    labels     = [row['period'].strftime('%Y-%m-%d') for row in period_data]
    counts     = [row['count'] for row in period_data]
    cumulative = list(itertools.accumulate(counts))

    return render(request, 'home.html', {
        'stats':            stats,
        'freq':             freq,
        'chart_labels':     labels,
        'chart_counts':     counts,
        'chart_cumulative': cumulative,
    })


@login_required
def qc_list(request):
    q_param  = request.GET.get('q', '').strip()
    status   = request.GET.get('status')
    decision = request.GET.get('decision')

    qs = QCEntry.objects.select_related('product')
    if q_param:
        qs = qs.filter(
            Q(product__name__icontains=q_param) |
            Q(batch_no__icontains=q_param) |
            Q(id__icontains=q_param)
        )
    if status in ['draft', 'pending_qc', 'qc_completed', 'cancelled']:
        qs = qs.filter(status=status)
    if decision in ['approved','approved_under_deviation','rejected']:
        qs = qs.filter(decision_status=decision)

    entries = qs.order_by('-entry_date', '-id')
    return render(request, 'qc/report.html', {
        'entries': entries,
        'q':        q_param,
        'status':   status,
        'decision': decision,
    })


@login_required
def qc_detail(request, pk):
    entry = get_object_or_404(QCEntry, pk=pk)
    spec_entries = SpecEntry.objects.filter(qc_entry=entry).select_related('spec')
    # pick the one group that was used
    # (you only ever created SpecEntry rows for that group)
    selected_group = ( spec_entries.values_list('spec__group', flat=True).distinct().first()) or ""
    return render(request, 'qc/qc_detail.html', {
        'entry':        entry,
        'spec_entries': spec_entries,
        'selected_group': selected_group,
    })


@login_required
def qc_create(request):
    """ add QC details (Permission Required: QC.add_qcentry) """
    if not request.user.has_perm('QC.add_qcentry'):
        logger.warning(f"Unauthorized Add attempt by {request.user.username}")
        messages.error(request, "You do not have permission to add QC records.")
        return redirect('indexpage')

    try:
        # 1) Sync BmrIssue from ERP once
        if not BmrIssue.objects.exists():
            with connections['readonly_db'].cursor() as cursor:
                cursor.execute(""" /* your ERP sync SQL... */ """)
                columns = [c[0] for c in cursor.description]
                rows = cursor.fetchall() or []
            to_create = []
            for row in rows:
                data = dict(zip(columns, row))
                to_create.append(BmrIssue(
                    bmr_issue_type = data['BMR_Issue_Type'],
                    bmr_issue_no   = data['BMR_Issue_No'],
                    bmr_issue_date = data['BMR_Issue_Date'],
                    fg_name        = data['FG_Name'],
                    op_batch_no    = data['OP_Batch_No'],
                    product_name   = data.get('Product_Name','') or '',
                    block          = data.get('Block','') or '',
                    line_no        = data['Line_No'],
                    item_type      = data['Item_Type'],
                    item_code      = data['Item_Code'],
                    item_name      = data['Item_Name'],
                    item_narration = data.get('Item_Narration','') or '',
                    uom            = data['UOM'],
                    batch_quantity = data['Batch_Quantity'],
                ))
            BmrIssue.objects.bulk_create(to_create)
            logger.info(f"BmrIssue sync: {len(to_create)} rows loaded from ERP by {request.user.username}")

        # 2) Batch dropdown
        distinct_batch_nos = (
            BmrIssue.objects
            .filter(bmr_issue_date__gte=date(2025, 1, 25))
            .values_list('op_batch_no', flat=True)
            .distinct().order_by('op_batch_no')
        )
        selected_batch_no = request.GET.get('batch_no_filter') or None
        if selected_batch_no:
            qc_query_results = BmrIssue.objects.filter(
                op_batch_no=selected_batch_no
            ).order_by('bmr_issue_no', 'line_no')
        else:
            qc_query_results = BmrIssue.objects.all().order_by('bmr_issue_no', 'line_no')

        equipment_list = LocalEquipmentMaster.objects.all().order_by('eqp_name')

        # 3) Stage dropdown (used for Stage → Product sync)
        stage_options = (
            Product.objects
            .exclude(stages__isnull=True)
            .exclude(stages__exact='')
            .values('stages', 'id')
            .distinct()
            .order_by('stages')
        )

        # Product dropdown (for showing product name)
        product_list = Product.objects.values('id', 'name').order_by('name')

        # 4) Form handling
        if request.method == 'POST':
            form = ProductionQCEntryForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    qc_entry = form.save(commit=False)
                    qc_entry.status = 'pending_qc'
                    qc_entry.created_by = request.user
                    qc_entry.save()

                    send_mail(
                        subject=f"[QC] New entry ready for QC: {qc_entry.product.name} / {qc_entry.batch_no}",
                        message=(
                            f"A new QCEntry (ID: {qc_entry.pk}) was submitted.\n"
                            f"Product: {qc_entry.product.name}\n"
                            f"Batch No: {qc_entry.batch_no}\n"
                            f"Stage: {qc_entry.get_stage_display()}\n"
                            f"Equipment: {qc_entry.equipment_id or '—'}\n"
                            f"Block: {qc_entry.block or '—'}\n"
                            f"Sample Description: {qc_entry.sample_description or '—'}\n"
                            f"Test Required For: {qc_entry.test_required_for or '—'}\n"
                        ),
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'it@ocspl.com'),
                        recipient_list=[
                            'shakir.s@ocspl.com',
                            'vinod.nimbalkar@ocspl.com',
                            'qc@ocspl.com',
                            'vikas.m@ocspl.com',
                            
                        ],
                        fail_silently=True,
                    )
                logger.info(f"QCEntry #{qc_entry.pk} created by {request.user.username} for product '{qc_entry.product.name}', batch {qc_entry.batch_no}")
                messages.success(request, "Header submitted. QC team has been notified.")
                return redirect('qc_list')
            else:
                logger.warning(f"QCEntry form validation failed by {request.user.username}. Errors: {form.errors}")
        else:
            now = timezone.now()
            form = ProductionQCEntryForm(initial={
                'entry_date': now,
                'sample_sent_at': now,  # Set initial value for sample_sent_at
            })

        return render(request, 'qc/qc_form_phase1.html', {
            'form':               form,
            'equipment_list':     equipment_list,
            'distinct_batch_nos': distinct_batch_nos,
            'selected_batch_no':  selected_batch_no,
            'stage_options':      stage_options,
            'product_list':       product_list,
            'qc_query_results':   qc_query_results,
        })
    except Exception as e:
        logger.error(f"Exception in qc_create by {request.user.username}: {e}", exc_info=True)
        messages.error(request, "An unexpected error occurred. Please contact the admin.")
        return redirect('qc_list')



@login_required
def qc_update(request, pk):
    try:
        qc_entry = get_object_or_404(QCEntry, pk=pk)
        reopen_to = request.GET.get('reopen')

        # ——— Handle “reopen” actions ———
        if reopen_to == 'prod' and qc_entry.status == 'qc_completed':
            qc_entry.status = 'draft'
            qc_entry.save()
            logger.info(f"QCEntry #{qc_entry.pk} reopened to Production by {request.user.username}")
            messages.success(request, "Entry reopened to Production.")
            return redirect('qc_update', pk=pk)

        if reopen_to == 'qc' and qc_entry.status == 'qc_completed':
            qc_entry.status = 'pending_qc'
            qc_entry.save()
            logger.info(f"QCEntry #{qc_entry.pk} reopened to QC by {request.user.username}")
            messages.success(request, "Entry reopened to QC.")
            return redirect('qc_update', pk=pk)

        # ——— Phase 1: Production header ———
        if qc_entry.status == 'draft':
            equipment_list     = LocalEquipmentMaster.objects.order_by('eqp_name')
            distinct_batch_nos = (
                BmrIssue.objects
                .filter(bmr_issue_date__gte=date(2025,1,25))
                .values_list('op_batch_no', flat=True)
                .distinct()
                .order_by('op_batch_no')
            )
            stage_options = (
                Product.objects
                       .exclude(stages__isnull=True)
                       .exclude(stages__exact='')
                       .values('stages','id')
                       .distinct()
                       .order_by('stages')
            )
            product_list = Product.objects.values('id','name').order_by('name')

            if request.method == 'POST':
                form = ProductionQCEntryForm(
                    request.POST,
                    instance=qc_entry,
                    stage_choices=stage_options,
                )
                if form.is_valid():
                    qc = form.save(commit=False)
                    qc.status = 'pending_qc'
                    qc.save()
                    logger.info(f"QCEntry #{qc.pk} updated by {request.user.username} (Production header → pending QC)")
                    messages.success(request, "Header updated and submitted to QC.")
                    return redirect('qc_list')
                messages.error(request, "Please correct the errors below.")
            else:
                form = ProductionQCEntryForm(
                    instance=qc_entry,
                    initial={'entry_date': timezone.localtime().strftime('%Y-%m-%dT%H:%M')},
                    stage_choices=stage_options,
                )

            return render(request, 'qc/qc_form_phase1.html', {
                'form':               form,
                'equipment_list':     equipment_list,
                'distinct_batch_nos': distinct_batch_nos,
                'stage_options':      stage_options,
                'product_list':       product_list,
            })

        # ——— Phase 2: QC results ———
        if qc_entry.status == 'pending_qc':
            existing_spec_entries = SpecEntry.objects.filter(qc_entry=qc_entry).select_related('spec')
            group_options = (
                Spec.objects
                    .filter(product=qc_entry.product)
                    .values_list('group', flat=True)
                    .distinct()
                    .order_by('group')
            )
            group_options = [g for g in group_options if g]  # drop empty

            if request.method == 'POST':
                results_form = QCResultsForm(request.POST, instance=qc_entry)
                results_form.fields['group'].choices = [("", "— Select Group —")] + [(g, g) for g in group_options]

                if results_form.is_valid():
                    with transaction.atomic():
                        qc = results_form.save(commit=False)

                        SpecEntry.objects.filter(qc_entry=qc).delete()
                        to_create = []
                        for key, raw in request.POST.items():
                            if not key.startswith('spec_result_'):
                                continue
                            sid = key.split('_')[-1]
                            try:
                                spec_obj = Spec.objects.get(pk=int(sid))
                            except (Spec.DoesNotExist, ValueError):
                                continue

                            raw = raw.strip()
                            remark = ''
                            if spec_obj.name == "Appearance" and raw:
                                ao, _ = AppearanceOption.objects.get_or_create(name=raw)
                                qc.product.appearance_options.add(ao)
                                remark = 'Pass' if request.POST.get(f'spec_pass_{sid}') else 'Fail'
                            elif spec_obj.min_val is not None and spec_obj.max_val is not None:
                                try:
                                    num = float(raw)
                                    remark = 'Pass' if spec_obj.min_val <= num <= spec_obj.max_val else 'Fail'
                                except ValueError:
                                    remark = ''

                            to_create.append(
                                SpecEntry(qc_entry=qc, spec=spec_obj, value=raw or None, remark=remark)
                            )
                        if to_create:
                            SpecEntry.objects.bulk_create(to_create)

                        qc.status = 'qc_completed'
                        qc.qc_completed_by = request.user
                        qc.save()
                        logger.info(f"QCEntry #{qc.pk} completed by {request.user.username} (QC results saved)")
                        
                        # ——— PDF + Email Attachment ———
                        try:
                            email_body = (
                                f"QCEntry (ID: {qc.pk}) completed on {timezone.localtime():%Y-%m-%d %H:%M}.\n"
                                f"Product: {qc.product.name}\n"
                                f"Batch No: {qc.batch_no}\n"
                                f"Stage: {qc.get_stage_display()}\n"
                                f"Equipment: {qc.equipment_id or '—'}\n"
                                f"Block: {qc.block or '—'}\n"
                                f"Sample Description: {qc.sample_description or '—'}\n"
                                f"Test Required For: {qc.test_required_for or '—'}\n\n"
                                "Please see the attached PDF for full details."
                            )

                            buffer = BytesIO()
                            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                            styles = getSampleStyleSheet()
                            story = []

                            story.append(Paragraph("QC Entry Details", styles['Title']))
                            story.append(Spacer(1, 12))
                            story.append(Paragraph("QC Completed", styles['Heading2']))
                            story.append(Spacer(1, 12))
                            story.append(Paragraph("Header Information", styles['Heading3']))
                            story.append(Spacer(1, 8))

                            cell_style = styles['BodyText']
                            cell_style.leading = 12

                            hdr_data = [
                                ['Entry No.', f"#{qc.id}"],
                                ['Product', qc.product.name],
                                ['Stage', qc.get_stage_display()],
                                ['Specification Group', qc.group or '—'],
                                ['General Remarks', Paragraph(qc.general_remarks or '—', cell_style)],
                                ['Batch No.', qc.batch_no],
                                ['AR No.', qc.ar_no],
                                ['Equipment', qc.equipment_id],
                                ['Block', qc.block],
                                ['Entry Date (Prod)', qc.entry_date.strftime("%Y-%m-%d %H:%M")],
                                ['Prepared By (Prod)', qc.created_by.get_full_name() if qc.created_by else '—'],
                                ['Sample Sent At', qc.sample_sent_at.strftime("%Y-%m-%d %H:%M") if qc.sample_sent_at else '—'],
                                ['Sample Description', qc.sample_description or '—'],
                                ['Sample Received At QC', qc.sample_received_at.strftime("%Y-%m-%d %H:%M") if qc.sample_received_at else '—'],
                                ['Released by QC At', qc.release_by_qc_at.strftime("%Y-%m-%d %H:%M") if qc.release_by_qc_at else '—'],
                                ['Completed By (QC)', qc.qc_completed_by.get_full_name() if qc.qc_completed_by else '—'],
                                ['Test Required For', qc.test_required_for or '—'],
                                ['Final QC Decision', qc.get_decision_status_display()],
                            ]

                            hdr_table = Table(hdr_data, colWidths=[150, 330])
                            hdr_table.setStyle(TableStyle([
                                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                                ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
                                ('BACKGROUND', (0,0), (0,0), colors.lightgrey),  # Gray background for "Entry No." label cell
                                ('BACKGROUND', (1,0), (1,0), colors.lightgrey), # Optional: lighter background for value cell
                            ]))
                            story.append(hdr_table)
                            story.append(Spacer(1, 24))

                            story.append(Paragraph(f"Test Parameter Results — Group: {qc.group}", styles['Heading3']))
                            story.append(Spacer(1, 8))
                            
                            specs_for_pdf = SpecEntry.objects.filter(qc_entry=qc, spec__group=qc.group).select_related('spec')
                            tbl_data = [[Paragraph('<b>#</b>', cell_style), Paragraph('<b>Specification</b>', cell_style), Paragraph('<b>Value</b>', cell_style), Paragraph('<b>Remark</b>', cell_style)]]
                            for idx, se in enumerate(specs_for_pdf, start=1):
                                 tbl_data.append([Paragraph(str(idx), cell_style), Paragraph(se.spec.name or '—', cell_style), Paragraph(se.value or '—', cell_style), Paragraph(se.remark or '—', cell_style)])

                            tbl = Table(tbl_data, colWidths=[30, 200, 150, 150], repeatRows=1)
                            tbl.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('GRID', (0,0), (-1,-1), 0.25, colors.grey)]))
                            story.append(tbl)
                            
                            doc.build(story)
                            pdf_data = buffer.getvalue()
                            buffer.close()
                            
                            email = EmailMessage(
                                subject=f"[QC Completed] Entry ID {qc.pk}", body=email_body, from_email=settings.DEFAULT_FROM_EMAIL,
                                to=[
                                'ganesh.t@ocspl.com',
                                'production.solapur@ocspl.com',
                                'vikas.m@ocspl.com',
                                ] # Updated recipient list
                            )
                            email.attach(f"QCEntry_{qc.pk}_details.pdf", pdf_data, "application/pdf")
                            email.send(fail_silently=False)

                        except Exception as e:
                            logger.error(f"Email failed for QCEntry #{qc.pk} after saving: {e}", exc_info=True)
                            messages.error(request, f"QC saved but email failed: {e}")

                    messages.success(request, "QC results saved. Production notified.")
                    return redirect('qc_detail', pk=qc.pk)
                
                messages.error(request, "Please correct the errors below.")
            else:
                results_form = QCResultsForm(instance=qc_entry)
                results_form.fields['group'].choices = [("", "— Select Group —")] + [(g, g) for g in group_options]

            return render(request, 'qc/qc_form_phase2.html', {
                'results_form':           results_form,
                'existing_spec_entries':  existing_spec_entries,
                'qc_entry':               qc_entry,
                'appearance_options':     AppearanceOption.objects.order_by('name'),
                'group_options':          group_options,
            })

        # ——— Prevent edits once completed ———
        if qc_entry.status == 'qc_completed':
            messages.error(request, "This QC entry is already completed. Use “Reopen” to edit.")
            return redirect('qc_detail', pk=pk)

        raise Http404("Invalid status for editing")

    except Exception as e:
        logger.error(f"Exception in qc_update for pk={pk} by {request.user.username}: {e}", exc_info=True)
        messages.error(request, "An unexpected error occurred. Please contact the admin.")
        return redirect('qc_list')


@login_required
def qc_delete(request, pk):
    qc = get_object_or_404(QCEntry, pk=pk)
    if request.method == 'POST':
        logger.info(f"QCEntry #{qc.pk} deleted by {request.user.username}")
        qc.delete()
        messages.success(request, "QC entry deleted.")
        return redirect('qc_list')
    else:
        logger.info(f"QCEntry #{qc.pk} delete confirmation page viewed by {request.user.username}")
    return render(request, 'qc/qc_confirm_delete.html', {'qc_entry': qc})


@login_required
def report(request):
    logger.info(f"User {request.user.username} accessed QC report page.")
    entries = (
        QCEntry.objects
        .select_related('product')
        .prefetch_related(Prefetch('values', queryset=SpecEntry.objects.select_related('spec'), to_attr='specs'))
        .order_by('-created')
    )
    return render(request, 'qc/report.html', {'entries': entries})


@require_GET
def get_product_details(request):
    product_id = request.GET.get('product')
    stage      = request.GET.get('stage')

    logger.info(f"AJAX get_product_details called by {request.user if hasattr(request, 'user') else 'Anonymous'} "
                f"for product_id={product_id}, stage={stage}")

    if not product_id:
        logger.warning("No product_id supplied in get_product_details.")
        return JsonResponse({'header': {}, 'specs': []}, status=200)

    try:
        pid = int(product_id)
        product = Product.objects.get(pk=pid)
    except (ValueError, Product.DoesNotExist):
        logger.error(f"Invalid product ID or product does not exist: {product_id}")
        return JsonResponse({'error': 'Invalid product or ID.'}, status=400)

    detail = None
    if stage:
        detail = LocalBOMDetail.objects.filter(
            item_name=product.name,
            fg_name=stage
        ).first()

    header_data = {
        'default_fg_name':  detail.fg_name  if detail else "",
        'default_bom_code': detail.bom_code if detail else "",
        'default_type':     detail.type     if detail else "",
    }

    # Added 'group' to values as requested
    specs_qs = Spec.objects.filter(product_id=pid).values('id','name','min_val','max_val','group')
    specs_list = list(specs_qs)

    logger.debug(f"Product details returned for product_id={product_id}: {header_data}, specs count={len(specs_list)}")
    return JsonResponse({'header': header_data, 'specs': specs_list}, status=200)



@require_GET
def get_specs(request):
    product_id = request.GET.get('product')
    logger.info(f"AJAX get_specs called by {request.user if hasattr(request, 'user') else 'Anonymous'} "
                f"for product_id={product_id}")
    if not product_id:
        logger.warning("No product_id supplied in get_specs.")
        return JsonResponse([], safe=False)
    try:
        pid = int(product_id)
        specs = Spec.objects.filter(product_id=pid).values('id','name','min_val','max_val')
        logger.debug(f"{specs.count()} specs returned for product_id={product_id}")
        return JsonResponse(list(specs), safe=False)
    except ValueError:
        logger.error(f"Invalid product ID (not integer): {product_id}")
        return JsonResponse({'error': 'Invalid product ID.'}, status=400)


@login_required
def item_master(request):
    logger.info(f"User {request.user.username} accessed Item Master.")
    items = LocalItemMaster.objects.all().order_by('product_name')
    return render(request, 'qc/item_master.html', {'item_list': items})


@login_required
def equipment_master(request):
    logger.info(f"User {request.user.username} accessed Equipment Master.")
    eq_list = LocalEquipmentMaster.objects.all().order_by('eqp_name')
    return render(request, 'qc/equipment_master.html', {'equipment_list': eq_list})


@login_required
def qc_reopen_for_qc(request, pk):
    logger.info(f"User {request.user.username} requested QC reopen for QCEntry {pk}.")
    qc = get_object_or_404(QCEntry, pk=pk)
    if qc.status != 'qc_completed':
        logger.warning(f"User {request.user.username} tried to reopen QCEntry {pk} for QC correction, but status is '{qc.status}'.")
        messages.error(request, "Only a completed entry can be reopened.")
        return redirect('qc_detail', pk=pk)
    SpecEntry.objects.filter(qc_entry=qc).delete()
    qc.status = 'pending_qc'
    qc.qc_completed_by = None
    qc.release_by_qc_at = None
    qc.save()
    logger.info(f"QCEntry {pk} reopened for QC correction by {request.user.username}.")
    messages.info(request, f"QC entry #{qc.pk} reopened for QC correction.")
    return redirect('qc_update', pk=pk)


@login_required
def qc_reopen_for_prod(request, pk):
    logger.info(f"User {request.user.username} requested Production reopen for QCEntry {pk}.")
    qc = get_object_or_404(QCEntry, pk=pk)
    if qc.status not in ('pending_qc','qc_completed'):
        logger.warning(f"User {request.user.username} tried to reopen QCEntry {pk} for production, but status is '{qc.status}'.")
        messages.error(request, "Only an entry in QC or completed can be reopened for Production.")
        return redirect('qc_detail', pk=pk)
    SpecEntry.objects.filter(qc_entry=qc).delete()
    qc.status = 'draft'
    qc.qc_completed_by = None
    qc.release_by_qc_at = None
    qc.save()
    logger.info(f"QCEntry {pk} reopened for production by {request.user.username}.")
    messages.info(request, f"QC entry #{qc.pk} reopened for Production.")
    return redirect('qc_update', pk=pk)


@login_required
def qc_cancel(request, pk):
    logger.info(f"User {request.user.username} attempted to cancel QCEntry {pk}.")
    qc = get_object_or_404(QCEntry, pk=pk)
    if qc.status == 'qc_completed':
        logger.warning(f"User {request.user.username} tried to cancel already completed QCEntry {pk}.")
        messages.error(request, "Cannot cancel: QC is already completed.")
    elif qc.status != 'cancelled':
        qc.status = 'cancelled'
        qc.save()
        logger.info(f"QCEntry {pk} cancelled by {request.user.username}.")
        messages.success(request, f"QC entry #{pk} cancelled.")
    return redirect('qc_list')



@login_required
def mis_report(request):
    """
    MIS report: one row per QCEntry,
    with dynamic columns for each SpecEntry, plus the saved 'group'.
    Supports CSV export including header block + table.
    """
    start_date  = request.GET.get('start_date')
    end_date    = request.GET.get('end_date')
    sel_product = request.GET.get('product')
    sel_batch   = request.GET.get('batch_no')
    sel_stage   = request.GET.get('stage')
    want_export = request.GET.get('export') == 'csv'

    logger.info(
        f"[MIS Report] User={request.user.username} Filters: "
        f"start_date={start_date}, end_date={end_date}, product={sel_product}, batch={sel_batch}, stage={sel_stage}, export={want_export}"
    )

    try:
        qs = QCEntry.objects.filter(status='qc_completed')
        if start_date:
            qs = qs.filter(entry_date__date__gte=start_date)
        if end_date:
            qs = qs.filter(entry_date__date__lte=end_date)
        if sel_product:
            qs = qs.filter(product_id=sel_product)
        if sel_batch:
            qs = qs.filter(batch_no=sel_batch)
        if sel_stage:
            qs = qs.filter(stage=sel_stage)

        qs = (
            qs.select_related('product')
              .prefetch_related(
                  Prefetch('values',
                           queryset=SpecEntry.objects.select_related('spec'),
                           to_attr='specs')
              )
              .order_by('entry_date')
        )

        # --- discover all spec names in order of appearance ---
        spec_names = []
        seen = set()
        for entry in qs:
            for se in entry.specs:
                n = se.spec.name
                if n not in seen:
                    seen.add(n)
                    spec_names.append(n)

        # --- assemble row dicts including the saved group ---
        rows = []
        for entry in qs:
            row = {
                'date':               entry.entry_date.strftime('%Y-%m-%d'),
                'product_name':       entry.product.name,
                'stage':              entry.stage or '',
                'group':              entry.group or '',           # Added group here
                'batch_no':           entry.batch_no or '',
                'reactor_no':         entry.equipment_id or '',
                'sample_description': entry.sample_description or '',
            }
            for se in entry.specs:
                row[se.spec.name] = se.value or ''
            rows.append(row)

        if want_export:
            filename = f"MIS_Report_{datetime.now():%Y%m%d_%H%M}.csv"
            logger.info(f"[MIS Report] User={request.user.username} triggered CSV export as {filename} (records={len(rows)}).")
            resp = HttpResponse(content_type='text/csv')
            resp['Content-Disposition'] = f'attachment; filename="{filename}"'
            writer = csv.writer(resp)

            # Header block
            writer.writerow(['MIS Report'])
            writer.writerow([
                'Product:',
                Product.objects.filter(pk=sel_product).first().name if sel_product else 'All',
                'Batch:', sel_batch or 'All',
                'Stage:', sel_stage or 'All'
            ])
            writer.writerow(['Date Range:', start_date or '-', 'to', end_date or '-'])
            writer.writerow(['Generated at:', datetime.now().strftime('%Y-%m-%d %H:%M')])
            writer.writerow([])

            # Added 'Group' column here
            headers = ['Date','Product','Stage','Group','Batch No.','Reactor No.','Sample Description'] + spec_names
            writer.writerow(headers)
            for r in rows:
                vals = [
                    r['date'],
                    r['product_name'],
                    r['stage'],
                    r['group'],                  # Added group here
                    r['batch_no'],
                    r['reactor_no'],
                    r['sample_description'],
                ] + [r.get(n, '') for n in spec_names]
                writer.writerow(vals)

            logger.info(f"[MIS Report] User={request.user.username} CSV export completed successfully.")
            return resp

        # Render HTML
        products = (
            QCEntry.objects
            .values('product__id', 'product__name')
            .distinct()
            .order_by('product__name')
        )
        batches = qs.values_list('batch_no', flat=True).distinct().order_by('batch_no')
        stages = QCEntry.objects.values_list('stage', flat=True).distinct().order_by('stage')

        logger.info(f"[MIS Report] User={request.user.username} viewed report page (records={len(rows)}).")

        return render(request, 'qc/mis_report.html', {
            'rows':         rows,
            'spec_names':   spec_names,
            'products':     products,
            'batches':      batches,
            'stages':       stages,
            'start_date':   start_date,
            'end_date':     end_date,
            'sel_product':  sel_product,
            'sel_batch':    sel_batch,
            'sel_stage':    sel_stage,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        })
    except Exception as e:
        logger.error(f"[MIS Report] User={request.user.username} error: {e}", exc_info=True)
        messages.error(request, "There was an error generating the MIS report.")
        return render(request, 'qc/mis_report.html', {})




@login_required
def sync_erp(request):
    """
    Trigger your ERP→Block sync on demand (only staff).
    Returns the full stdout of the management command.
    """
    buf = StringIO()
    try:
        call_command('sync_erp', stdout=buf, stderr=buf)
        output = buf.getvalue()
        return JsonResponse({'status': 'ok', 'log': output})
    except Exception as e:
        # include any traceback / error text
        buf.write(f"\nERROR: {e}")
        return JsonResponse({'status': 'error', 'log': buf.getvalue()}, status=500)

