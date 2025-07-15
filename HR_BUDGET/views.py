from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from HR_BUDGET.models import *
from HR_BUDGET.forms import (ContractorWagesForm,SecurityWagesForm,HrBudgetWelfareForm,
                             HrBudgetCanteenForm,HrBudgetMedicalForm,HrBudgetVehicleForm,HrBudgetTravellingForm,
                             HRBudgetGuestHouseForm, HRBudgetGeneralAdminForm,HRBudgetCommunicationForm,InsuranceMediclaimForm,
                             HRBudgetAMCForm,HRBudgetTrainingForm)
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Sum, F, Value, Min, Max
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone
from decimal import Decimal
import datetime
from django import forms
from django.db.models.functions import TruncWeek
from django.db.models import DateField
import io
import xlsxwriter
from django.http import HttpResponse


# Add Contractor Wages
@login_required
def add_contractor_wages(request):
    if request.method == 'POST':
        form = ContractorWagesForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Contractor wage record added successfully!")
            return redirect('add_contractor_wages')  # Replace with your list view name or success page
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContractorWagesForm()
    return render(request, 'hrbudget/contractor/contractorwages_form.html', {'form': form,'active_link': 'contractor_wages'})


@login_required
def contractorwages_list(request):
    records = ContractorWages.objects.order_by('-invoice_date')
    paginator = Paginator(records, 10)  # 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        'hrbudget/contractor/contractorwages_list.html',
        {
            'page_obj': page_obj,
            'active_link': 'contractor_wages'
        }
    )


@login_required
def edit_contractor_wages(request, pk):
    from .models import ContractorWages  # adjust if needed
    obj = ContractorWages.objects.get(pk=pk)
    if request.method == 'POST':
        form = ContractorWagesForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Contractor wage record updated successfully!")
            return redirect('contractorwages_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContractorWagesForm(instance=obj)
    return render(request, 'hrbudget/contractor/contractorwages_form.html', {
        'form': form,
        'active_link': 'contractor_wages',
        'is_edit': True,  # this will let the template know we're editing
        'object': obj,    # in case you want to show details
    })



@login_required
def delete_contractor_wages(request, pk):
    from .models import ContractorWages  # adjust if needed
    obj = ContractorWages.objects.get(pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Contractor wage record deleted successfully!")
        return redirect('contractorwages_list')
    return redirect('contractorwages_list')



# Add Security Wages
@login_required
def add_security_wages(request):
    if request.method == 'POST':
        form = SecurityWagesForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Security wage record added successfully!")
            return redirect('add_security_wages')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SecurityWagesForm()
    return render(request, 'hrbudget/security/securitywages_form.html', {'form': form,'active_link': 'security_wages'})


@login_required
def securitywages_list(request):
    records = SecurityWages.objects.order_by('-invoice_date', '-id')
    paginator = Paginator(records, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'hrbudget/security/securitywages_list.html', {
        'page_obj': page_obj,
        'active_link': 'security_wages',
    })


@login_required
def edit_security_wages(request, pk):
    obj = get_object_or_404(SecurityWages, pk=pk)
    if request.method == 'POST':
        form = SecurityWagesForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Security wage record updated successfully!")
            return redirect('securitywages_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SecurityWagesForm(instance=obj)
    return render(request, 'hrbudget/security/securitywages_form.html', {'form': form,'active_link': 'security_wages'})


@login_required
def delete_security_wages(request, pk):
    obj = get_object_or_404(SecurityWages, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Security wage record deleted successfully!")
        return redirect('securitywages_list')
    # Optional: Redirect even on GET, for safety
    return redirect('securitywages_list')




# Add HR Budget Welfare
@login_required
def add_hrbudget_welfare(request):
    if request.method == 'POST':
        form = HrBudgetWelfareForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Welfare budget record added successfully!")
            return redirect('add_hrbudget_welfare')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HrBudgetWelfareForm()
    return render(request, 'hrbudget/welfare/hrbudgetwelfare_form.html', {'form': form,'active_link': 'welfare'})



@login_required
def hrbudget_welfare_list(request):
    records = HrBudgetWelfare.objects.order_by('-invoice_date', '-id')
    return render(request, 'hrbudget/welfare/hrbudgetwelfare_list.html', {'records': records,'active_link': 'welfare'})



@login_required
def edit_hrbudget_welfare(request, pk):
    obj = get_object_or_404(HrBudgetWelfare, pk=pk)
    if request.method == 'POST':
        form = HrBudgetWelfareForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Welfare record updated successfully!")
            return redirect('hrbudget_welfare_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HrBudgetWelfareForm(instance=obj)
    return render(request, 'hrbudget/welfare/hrbudgetwelfare_form.html', {'form': form, 'active_link': 'welfare'})


@login_required
def delete_hrbudget_welfare(request, pk):
    obj = get_object_or_404(HrBudgetWelfare, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Welfare record deleted successfully!")
        return redirect('hrbudget_welfare_list')
    return redirect('hrbudget_welfare_list')



# Add HR Budget Canteen
@login_required
def add_hrbudget_canteen(request):
    if request.method == 'POST':
        form = HrBudgetCanteenForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Canteen budget record added successfully!")
            return redirect('add_hrbudget_canteen')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HrBudgetCanteenForm()
    return render(request, 'hrbudget/canteen/hrbudgetcanteen_form.html', {'form': form,'active_link': 'canteen'})



@login_required
def hrbudget_canteen_list(request):
    records = HrBudgetCanteen.objects.order_by('-invoice_date', '-id')
    paginator = Paginator(records, 10)  # 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        'hrbudget/canteen/hrbudgetcanteen_list.html',
        {
            'page_obj': page_obj,
            'active_link': 'canteen'
        }
    )


@login_required
def edit_hrbudget_canteen(request, pk):
    obj = get_object_or_404(HrBudgetCanteen, pk=pk)
    if request.method == 'POST':
        form = HrBudgetCanteenForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Canteen record updated successfully!")
            return redirect('hrbudget_canteen_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HrBudgetCanteenForm(instance=obj)
    return render(request, 'hrbudget/canteen/hrbudgetcanteen_form.html', {'form': form, 'active_link': 'canteen'})



@login_required
def delete_hrbudget_canteen(request, pk):
    obj = get_object_or_404(HrBudgetCanteen, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Canteen record deleted successfully!")
        return redirect('hrbudget_canteen_list')
    return redirect('hrbudget_canteen_list')


# Add HR Budget Medical
@login_required
def add_hrbudget_medical(request):
    if request.method == 'POST':
        form = HrBudgetMedicalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Medical budget record added successfully!")
            return redirect('add_hrbudget_medical')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HrBudgetMedicalForm()
    return render(request, 'hrbudget/medical/hrbudgetmedical_form.html', {'form': form,'active_link': 'medical'})


@login_required
def hrbudget_medical_list(request):
    records = HrBudgetMedical.objects.all().order_by('-invoice_date', '-id')
    return render(request, 'hrbudget/medical/hrbudgetmedical_list.html', {'records': records})



@login_required
def edit_hrbudget_medical(request, pk):
    obj = get_object_or_404(HrBudgetMedical, pk=pk)
    if request.method == 'POST':
        form = HrBudgetMedicalForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Medical budget record updated successfully!")
            return redirect('hrbudget_medical_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HrBudgetMedicalForm(instance=obj)
    return render(request, 'hrbudget/medical/hrbudgetmedical_form.html', {
        'form': form, 'active_link': 'medical'
    })



@login_required
def delete_hrbudget_medical(request, pk):
    obj = get_object_or_404(HrBudgetMedical, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Medical budget record deleted successfully!")
        return redirect('hrbudget_medical_list')
    return redirect('hrbudget_medical_list')


@login_required
def add_hrbudget_vehicle(request):
    if request.method == 'POST':
        form = HrBudgetVehicleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle budget record added successfully!")
            return redirect('add_hrbudget_vehicle')  # Or use your vehicle list page URL name
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HrBudgetVehicleForm()
    return render(request, 'hrbudget/vehicle/hrbudgetvehicle_form.html', {
        'form': form,
        'active_link': 'vehicle'
    })


@login_required
def hrbudget_vehicle_list(request):
    records = HrBudgetVehicle.objects.all().order_by('-invoice_date', '-id')
    return render(request, 'hrbudget/vehicle/hrbudgetvehicle_list.html', {'records': records,'active_link': 'vehicle'})


@login_required
def edit_hrbudget_vehicle(request, pk):
    obj = get_object_or_404(HrBudgetVehicle, pk=pk)
    if request.method == 'POST':
        form = HrBudgetVehicleForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle budget record updated successfully!")
            return redirect('hrbudget_vehicle_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HrBudgetVehicleForm(instance=obj)
    return render(request, 'hrbudget/vehicle/hrbudgetvehicle_form.html', {
        'form': form,
        'active_link': 'vehicle'
    })



@login_required
def delete_hrbudget_vehicle(request, pk):
    obj = get_object_or_404(HrBudgetVehicle, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Vehicle budget record deleted successfully!")
        return redirect('hrbudget_vehicle_list')
    return redirect('hrbudget_vehicle_list')


@login_required
def add_hrbudget_travelling_lodging(request):
    if request.method == 'POST':
        form = HrBudgetTravellingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Travelling/Lodging/Boarding record added successfully!")
            return redirect('add_hrbudget_travelling_lodging')  # Change to your list view name if needed
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HrBudgetTravellingForm()
    return render(request, 'hrbudget/travelling/hrbudgettravelling_form.html', {
        'form': form,
        'active_link': 'travelling_lodging_boarding'
    })


@login_required
def hrbudget_travelling_lodging_list(request):
    records = HrBudgetTravellingLodging.objects.all().order_by('-invoice_date', '-id')
    paginator = Paginator(records, 10)  # Show 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'hrbudget/travelling/hrbudgettravelling_list.html', {
        'page_obj': page_obj,
        'active_link': 'travelling_lodging_boarding'
    })


@login_required
def edit_hrbudget_travelling_lodging(request, pk):
    obj = get_object_or_404(HrBudgetTravellingLodging, pk=pk)
    if request.method == 'POST':
        form = HrBudgetTravellingForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Travelling/Lodging/Boarding record updated successfully!")
            return redirect('hrbudget_travelling_lodging_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HrBudgetTravellingForm(instance=obj)
    return render(request, 'hrbudget/travelling/hrbudgettravelling_form.html', {
        'form': form,
        'active_link': 'travelling_lodging_boarding'
    })

@login_required
def delete_hrbudget_travelling_lodging(request, pk):
    obj = get_object_or_404(HrBudgetTravellingLodging, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Travelling/Lodging/Boarding record deleted successfully!")
        return redirect('hrbudget_travelling_lodging_list')
    return redirect('hrbudget_travelling_lodging_list')



@login_required
def add_hrbudget_guesthouse(request):
    if request.method == 'POST':
        form = HRBudgetGuestHouseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Guest House record added successfully!")
            return redirect('add_hrbudget_guesthouse')  # Or your guest house list view
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HRBudgetGuestHouseForm()
    return render(request, 'hrbudget/guesthouse/hrbudgetguesthouse_form.html', {
        'form': form,
        'active_link': 'guest_house'
    })


@login_required
def hrbudget_guesthouse_list(request):
    records = HRBudgetGuestHouse.objects.all().order_by('-invoice_date', '-id')
    return render(request, 'hrbudget/guesthouse/hrbudgetguesthouse_list.html', {'records': records,'active_link': 'guest_house'})


@login_required
def edit_hrbudget_guesthouse(request, pk):
    obj = get_object_or_404(HRBudgetGuestHouse, pk=pk)
    if request.method == 'POST':
        form = HRBudgetGuestHouseForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Guest House record updated successfully!")
            return redirect('hrbudget_guesthouse_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HRBudgetGuestHouseForm(instance=obj)
    return render(request, 'hrbudget/guesthouse/hrbudgetguesthouse_form.html', {
        'form': form,
        'active_link': 'guest_house'
    })

@login_required
def delete_hrbudget_guesthouse(request, pk):
    obj = get_object_or_404(HRBudgetGuestHouse, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Guest House record deleted successfully!")
        return redirect('hrbudget_guesthouse_list')
    return redirect('hrbudget_guesthouse_list')



@login_required
def add_hrbudget_general_admin(request):
    if request.method == 'POST':
        form = HRBudgetGeneralAdminForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "General Admin budget record added successfully!")
            return redirect('add_hrbudget_general_admin')  # Or use your list view url
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HRBudgetGeneralAdminForm()
    return render(request, 'hrbudget/generaladmin/generaladmin_form.html', {
        'form': form,
        'active_link': 'general_admin'
    })


@login_required
def hrbudget_general_admin_list(request):
    records = HRBudgetGeneralAdmin.objects.all().order_by('-invoice_date', '-id')
    return render(request, 'hrbudget/generaladmin/generaladmin_list.html', {'records': records,'active_link': 'general_admin'})



@login_required
def edit_hrbudget_general_admin(request, pk):
    obj = get_object_or_404(HRBudgetGeneralAdmin, pk=pk)
    if request.method == 'POST':
        form = HRBudgetGeneralAdminForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "General Admin budget record updated successfully!")
            return redirect('hrbudget_general_admin_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HRBudgetGeneralAdminForm(instance=obj)
    return render(request, 'hrbudget/generaladmin/generaladmin_form.html', {
        'form': form,
        'active_link': 'general_admin'
    })

@login_required
def delete_hrbudget_general_admin(request, pk):
    obj = get_object_or_404(HRBudgetGeneralAdmin, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "General Admin budget record deleted successfully!")
        return redirect('hrbudget_general_admin_list')
    return redirect('hrbudget_general_admin_list')



@login_required
def add_hrbudget_communication(request):
    if request.method == 'POST':
        form = HRBudgetCommunicationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Communication budget record added successfully!")
            return redirect('add_hrbudget_communication')  # or use your list page: 'hrbudget_communication_list'
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HRBudgetCommunicationForm()
    return render(request, 'hrbudget/communication/hrbudgetcommunication_form.html', {
        'form': form,
        'active_link': 'communication'
    })


@login_required
def edit_hrbudget_communication(request, pk):
    obj = get_object_or_404(HRBudgetCommunication, pk=pk)
    if request.method == 'POST':
        form = HRBudgetCommunicationForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Communication budget record updated successfully!")
            return redirect('hrbudget_communication_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HRBudgetCommunicationForm(instance=obj)
    return render(request, 'hrbudget/communication/hrbudgetcommunication_form.html', {
        'form': form,
        'active_link': 'communication'
    })


@login_required
def delete_hrbudget_communication(request, pk):
    obj = get_object_or_404(HRBudgetCommunication, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Communication budget record deleted successfully!")
        return redirect('hrbudget_communication_list')
    return redirect('hrbudget_communication_list')


@login_required
def hrbudget_communication_list(request):
    records = HRBudgetCommunication.objects.all().order_by('-invoice_date', '-id')
    return render(request, 'hrbudget/communication/hrbudgetcommunication_list.html', {
        'records': records,
        'active_link': 'communication'
    })



@login_required
def add_insurance_mediclaim(request):
    if request.method == 'POST':
        form = InsuranceMediclaimForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Insurance Mediclaim record added successfully!")
            return redirect('insurance_mediclaim_list')  # Change to your list view name
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = InsuranceMediclaimForm()

    return render(request, 'hrbudget/insurance_mediclaim/add_insurance_mediclaim_form.html', {
        'form': form,
        'active_link': 'insurance_mediclaim',
    })


@login_required
def edit_insurance_mediclaim(request, pk):
    obj = get_object_or_404(InsuranceMediclaim, pk=pk)
    if request.method == 'POST':
        form = InsuranceMediclaimForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Insurance Mediclaim record updated successfully!")
            return redirect('insurance_mediclaim_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = InsuranceMediclaimForm(instance=obj)
    return render(request, 'hrbudget/insurance_mediclaim/add_insurance_mediclaim_form.html', {  # Use same template as add
        'form': form,
        'active_link': 'insurance_mediclaim',
    })
\
@login_required
def insurance_mediclaim_list(request):
    records = InsuranceMediclaim.objects.order_by('-invoice_date', '-id')
    paginator = Paginator(records, 10)  # 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'hrbudget/insurance_mediclaim/insurance_mediclaim_list.html', {
        'page_obj': page_obj,
        'active_link': 'insurance_mediclaim',
    })



@login_required
def delete_insurance_mediclaim(request, pk):
    obj = get_object_or_404(InsuranceMediclaim, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Insurance Mediclaim record deleted successfully!")
        return redirect('insurance_mediclaim_list')
    # For GET request, optionally redirect or show confirmation page
    return redirect('insurance_mediclaim_list')



@login_required
def add_hrbudget_amc(request):
    if request.method == 'POST':
        form = HRBudgetAMCForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "AMC record added successfully!")
            return redirect('hrbudget_amc_list')  # Update with your list view name
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HRBudgetAMCForm()

    return render(request, 'hrbudget/amc/amc_form.html', {
        'form': form,
        'active_link': 'hrbudget_amc',
    })



@login_required
def edit_hrbudget_amc(request, pk):
    obj = get_object_or_404(HRBudgetAMC, pk=pk)
    if request.method == 'POST':
        form = HRBudgetAMCForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "AMC record updated successfully!")
            return redirect('hrbudget_amc_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HRBudgetAMCForm(instance=obj)
    return render(request, 'hrbudget/amc/amc_form.html', {
        'form': form,
        'active_link': 'hrbudget_amc',
    })

@login_required
def delete_hrbudget_amc(request, pk):
    obj = get_object_or_404(HRBudgetAMC, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "AMC record deleted successfully!")
        return redirect('hrbudget_amc_list')
    return redirect('hrbudget_amc_list')



@login_required
def hrbudget_amc_list(request):
    records = HRBudgetAMC.objects.order_by('-invoice_date', '-id')
    paginator = Paginator(records, 10)  # 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'hrbudget/amc/amc_list.html', {
        'page_obj': page_obj,
        'active_link': 'hrbudget_amc',
    })



@login_required
def add_hrbudget_training(request):
    if request.method == 'POST':
        form = HRBudgetTrainingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Training record added successfully!")
            return redirect('hrbudget_training_list')  # Update with your list view name
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HRBudgetTrainingForm()

    return render(request, 'hrbudget/training/training_form.html', {
        'form': form,
        'active_link': 'hrbudget_training',
    })



@login_required
def edit_hrbudget_training(request, pk):
    obj = get_object_or_404(HRBudgetTraining, pk=pk)
    if request.method == 'POST':
        form = HRBudgetTrainingForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Training record updated successfully!")
            return redirect('hrbudget_training_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HRBudgetTrainingForm(instance=obj)
    return render(request, 'hrbudget/training/training_form.html', {
        'form': form,
        'active_link': 'hrbudget_training',
    })

@login_required
def delete_hrbudget_training(request, pk):
    obj = get_object_or_404(HRBudgetTraining, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Training record deleted successfully!")
        return redirect('hrbudget_training_list')
    return redirect('hrbudget_training_list')



@login_required
def hrbudget_training_list(request):
    records = HRBudgetTraining.objects.order_by('-invoice_date', '-id')
    paginator = Paginator(records, 10)  # 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'hrbudget/training/training_list.html', {
        'page_obj': page_obj,
        'active_link': 'hrbudget_training',
    })


# ==========================Dashboard==================================================


class PeriodFilterForm(forms.Form):
    PERIOD_CHOICES = [
        ('monthly', 'Monthly'),
        ('weekly', 'Weekly'),
        ('daily', 'Daily'),
    ]
    period_type = forms.ChoiceField(choices=PERIOD_CHOICES, required=True)
    from_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    to_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))


def get_date_headers(period_type, min_date, max_date, from_date=None, to_date=None):
    headers = []
    if period_type == 'monthly':
        months = get_month_range_local(min_date, max_date)
        headers = [{'date_obj': m, 'display': m.strftime("%b-%y")} for m in months]
    elif period_type == 'weekly':
        weeks = []
        d = min_date
        while d <= max_date:
            week_start = d - datetime.timedelta(days=d.weekday())  # Monday
            week_end = week_start + datetime.timedelta(days=6)
            if week_start < min_date:
                week_start = min_date
            if week_end > max_date:
                week_end = max_date
            if not weeks or weeks[-1]['date_obj'] != week_start:
                # Format as (30Mar-5Apr)
                week_display = f"{week_start.strftime('%d%b')}-{week_end.strftime('%d%b')}"
                weeks.append({'date_obj': week_start, 'week_end': week_end, 'display': week_display})
            d = week_end + datetime.timedelta(days=1)
        headers = weeks
    elif period_type == 'daily' and from_date and to_date:
        d = from_date
        while d <= to_date:
            headers.append({'date_obj': d, 'display': d.strftime("%d-%b-%y")})
            d += datetime.timedelta(days=1)
    return headers


def get_month_range_local(start_date, end_date):
    months = []
    if not start_date or not end_date:
        return []
    current_date = datetime.date(start_date.year, start_date.month, 1)
    end_month_start = datetime.date(end_date.year, end_date.month, 1)
    while current_date <= end_month_start:
        months.append(current_date)
        year = current_date.year + (current_date.month // 12)
        month = current_date.month % 12 + 1
        current_date = datetime.date(year, month, 1)
    return months



def monthly_hr_budget_summary(request):
    model_configs = [
        ("Contractor Wages", ContractorWages, 'contractor_name', 'contractor_wages'),
        ("Security Wages", SecurityWages, 'contractor_name', 'security_wages'),
        ("Welfare", HrBudgetWelfare, 'welfare_name', 'welfare'),
        ("Canteen", HrBudgetCanteen, 'name', 'canteen'),
        ("Medical Expenses", HrBudgetMedical, 'doctor_hospital_name', 'medical'),
        ("Vehicle Expenses", HrBudgetVehicle, 'vehicle_name', 'vehicle'),
        ("Travelling & Lodging", HrBudgetTravellingLodging, 'name', 'travelling_lodging'),
        ("Guest House Expenses", HRBudgetGuestHouse, 'name', 'guesthouse'),
        ("General Admin Expenses", HRBudgetGeneralAdmin, 'category', 'general_admin'),
        ("Communication Expenses", HRBudgetCommunication, 'invoice_name', 'communication'),
        ("Insurance Mediclaim", InsuranceMediclaim, 'category', 'insurance_mediclaim'),
        ("AMC", HRBudgetAMC, 'amc_name', 'AMC'),
        ("Training", HRBudgetTraining, 'name', 'Training'),
    ]

    # Filter form
    form = PeriodFilterForm(request.GET or None)
    period_type = 'monthly'
    from_date = to_date = None

    if form.is_valid():
        period_type = form.cleaned_data.get('period_type', 'monthly')
        from_date = form.cleaned_data.get('from_date')
        to_date = form.cleaned_data.get('to_date')

    # Compute min/max date across models
    min_date, max_date = None, None
    for _, model_class, _, _ in model_configs:
        if model_class.objects.exists():
            dates = model_class.objects.aggregate(min_inv_date=Min('invoice_date'), max_inv_date=Max('invoice_date'))
            if dates['min_inv_date']:
                min_date = dates['min_inv_date'] if min_date is None else min(min_date, dates['min_inv_date'])
            if dates['max_inv_date']:
                max_date = dates['max_inv_date'] if max_date is None else max(max_date, dates['max_inv_date'])
    if not min_date or not max_date:
        today = timezone.now().date()
        min_date = today.replace(day=1)
        max_date = today

    # Override min/max for daily period
    if period_type == 'daily' and from_date and to_date and from_date <= to_date:
        min_date, max_date = from_date, to_date

    month_headers = get_date_headers(period_type, min_date, max_date, from_date, to_date)
    processed_rows = []
    category_index = 0

    # Initialize grand totals dict
    grand_totals = {h['date_obj']: Decimal('0.00') for h in month_headers}

    # ----- MAIN QUERY LOOP -----
    for cat_display_name, model_class, item_field_name, _ in model_configs:
        current_category_totals = {h['date_obj']: Decimal('0.00') for h in month_headers}

        # Select grouping annotation based on period
        if period_type == 'monthly':
            group_by = TruncMonth('invoice_date')
        elif period_type == 'weekly':
            group_by = TruncWeek('invoice_date', output_field=DateField())
        else:  # daily
            group_by = F('invoice_date')

        queryset = model_class.objects.annotate(
            period=group_by,
            item_name_val=F(item_field_name),
            total_amount=Coalesce(F('bill_amount'), Value(Decimal('0.00')))
        ).values('period', 'item_name_val').annotate(
            period_sum=Sum('total_amount')
        ).order_by('period', 'item_name_val')

        item_map = {}
        for entry in queryset:
            period_obj = entry['period']
            item_name = entry['item_name_val']
            amount = entry['period_sum'] or Decimal('0.00')
            if item_name not in item_map:
                item_map[item_name] = {h['date_obj']: Decimal('0.00') for h in month_headers}
            if period_obj in item_map[item_name]:
                item_map[item_name][period_obj] = amount
            if period_obj in current_category_totals:
                current_category_totals[period_obj] += amount

        # Accumulate grand totals
        for period_key, amount in current_category_totals.items():
            grand_totals[period_key] += amount

        category_index += 1
        category_id_for_html = f"cat-{category_index}"
        processed_rows.append({
            'type': 'category',
            'html_id': category_id_for_html,
            'data_category_id': category_id_for_html,
            'name': cat_display_name,
            'monthly_values': current_category_totals,
        })
        sorted_item_names = sorted(item_map.keys())
        for item_name in sorted_item_names:
            processed_rows.append({
                'type': 'item',
                'parent_category_id': category_id_for_html,
                'name': item_name,
                'monthly_values': item_map[item_name]
            })

    # Append Grand Total row
    processed_rows.append({
        'type': 'grand_total',
        'name': 'Grand Total',
        'monthly_values': grand_totals,
    })

    context = {
        'report_title': "Monthly HR Budget Summary",
        'month_headers': month_headers,
        'processed_rows': processed_rows,
        'filter_form': form,
        'period_type': period_type,
        'active_link': 'dashboard'
    }
    return render(request, 'hrbudget/hr_budget_summary.html', context)


def download_hr_budget_excel(request):
    # ------- Copy filter/generation logic from monthly_hr_budget_summary -------
    model_configs = [
        ("Contractor Wages", ContractorWages, 'contractor_name', 'contractor_wages'),
        ("Security Wages", SecurityWages, 'contractor_name', 'security_wages'),
        ("Welfare", HrBudgetWelfare, 'welfare_name', 'welfare'),
        ("Canteen", HrBudgetCanteen, 'name', 'canteen'),
        ("Medical Expenses", HrBudgetMedical, 'doctor_hospital_name', 'medical'),
        ("Vehicle Expenses", HrBudgetVehicle, 'vehicle_name', 'vehicle'),
        ("Travelling & Lodging", HrBudgetTravellingLodging, 'name', 'travelling_lodging'),
        ("Guest House Expenses", HRBudgetGuestHouse, 'name', 'guesthouse'),
        ("General Admin Expenses", HRBudgetGeneralAdmin, 'category', 'general_admin'),
        ("Communication Expenses", HRBudgetCommunication, 'invoice_name', 'communication'),
        ("Insurance Mediclaim", InsuranceMediclaim, 'category', 'insurance_mediclaim'),
        ("AMC", HRBudgetAMC, 'amc_name', 'AMC'),
        ("Training", HRBudgetTraining, 'name', 'Training'),
    ]
    form = PeriodFilterForm(request.GET or None)
    period_type = 'monthly'
    from_date = to_date = None
    if form.is_valid():
        period_type = form.cleaned_data.get('period_type', 'monthly')
        from_date = form.cleaned_data.get('from_date')
        to_date = form.cleaned_data.get('to_date')

    # Min/max logic
    min_date, max_date = None, None
    for _, model_class, _, _ in model_configs:
        if model_class.objects.exists():
            dates = model_class.objects.aggregate(min_inv_date=Min('invoice_date'), max_inv_date=Max('invoice_date'))
            if dates['min_inv_date']:
                min_date = dates['min_inv_date'] if min_date is None else min(min_date, dates['min_inv_date'])
            if dates['max_inv_date']:
                max_date = dates['max_inv_date'] if max_date is None else max(max_date, dates['max_inv_date'])
    if not min_date or not max_date:
        today = timezone.now().date()
        min_date = today.replace(day=1)
        max_date = today
    if period_type == 'daily' and from_date and to_date and from_date <= to_date:
        min_date, max_date = from_date, to_date

    month_headers = get_date_headers(period_type, min_date, max_date, from_date, to_date)

    # Data processing (same as above)
    processed_rows = []
    category_index = 0

    # Initialize grand totals dict
    grand_totals = {h['date_obj']: Decimal('0.00') for h in month_headers}

    for cat_display_name, model_class, item_field_name, _ in model_configs:
        current_category_totals = {h['date_obj']: Decimal('0.00') for h in month_headers}
        if period_type == 'monthly':
            group_by = TruncMonth('invoice_date')
        elif period_type == 'weekly':
            group_by = TruncWeek('invoice_date', output_field=DateField())
        else:  # daily
            group_by = F('invoice_date')
        queryset = model_class.objects.annotate(
            period=group_by,
            item_name_val=F(item_field_name),
            total_amount=Coalesce(F('bill_amount'), Value(Decimal('0.00')))
        ).values('period', 'item_name_val').annotate(
            period_sum=Sum('total_amount')
        ).order_by('period', 'item_name_val')
        item_map = {}
        for entry in queryset:
            period_obj = entry['period']
            item_name = entry['item_name_val']
            amount = entry['period_sum'] or Decimal('0.00')
            if item_name not in item_map:
                item_map[item_name] = {h['date_obj']: Decimal('0.00') for h in month_headers}
            if period_obj in item_map[item_name]:
                item_map[item_name][period_obj] = amount
            if period_obj in current_category_totals:
                current_category_totals[period_obj] += amount

        # Accumulate grand totals
        for period_key, amount in current_category_totals.items():
            grand_totals[period_key] += amount

        category_index += 1
        processed_rows.append({
            'type': 'category',
            'name': cat_display_name,
            'monthly_values': current_category_totals,
        })
        sorted_item_names = sorted(item_map.keys())
        for item_name in sorted_item_names:
            processed_rows.append({
                'type': 'item',
                'name': item_name,
                'monthly_values': item_map[item_name]
            })

    # ------- Generate Excel file in-memory -------
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('HR Budget Summary')

    # Formats
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#C6E0B4', 'border': 1})
    category_fmt = workbook.add_format({'bold': True, 'bg_color': '#E2EFDA', 'border': 1})
    item_fmt = workbook.add_format({'border': 1})
    currency_fmt = workbook.add_format({'num_format': '#,##,##0.00', 'border': 1})
    grand_total_fmt = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1, 'num_format': '#,##,##0.00'})

    # Write headers
    worksheet.write(0, 0, 'Name', header_fmt)
    for idx, mh in enumerate(month_headers):
        worksheet.write(0, idx+1, mh['display'], header_fmt)

    row_idx = 1
    for row_data in processed_rows:
        if row_data['type'] == 'category':
            worksheet.write(row_idx, 0, row_data['name'], category_fmt)
            for col_idx, mh in enumerate(month_headers):
                val = row_data['monthly_values'].get(mh['date_obj'], Decimal('0.00'))
                worksheet.write_number(row_idx, col_idx+1, float(val), workbook.add_format({
                    'bold': True, 'bg_color': '#E2EFDA', 'border': 1, 'num_format': '#,##,##0.00'
                }))
        else:
            worksheet.write(row_idx, 0, row_data['name'], item_fmt)
            for col_idx, mh in enumerate(month_headers):
                val = row_data['monthly_values'].get(mh['date_obj'], Decimal('0.00'))
                worksheet.write_number(row_idx, col_idx+1, float(val), currency_fmt)
        row_idx += 1

    # Write Grand Total row at the end
    worksheet.write(row_idx, 0, 'Grand Total', grand_total_fmt)
    for col_idx, mh in enumerate(month_headers):
        val = grand_totals.get(mh['date_obj'], Decimal('0.00'))
        worksheet.write_number(row_idx, col_idx+1, float(val), grand_total_fmt)

    # Optional: set column widths for better appearance
    worksheet.set_column(0, 0, 32)  # Name column wider
    worksheet.set_column(1, len(month_headers), 18)  # Data columns

    workbook.close()
    output.seek(0)
    filename = 'HR_Budget_Summary.xlsx'
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response

