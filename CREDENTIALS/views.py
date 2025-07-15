from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from .forms import CredentialApplicationForm
from django.core.paginator import Paginator
from .models import Credentials


def credential_add(request):
    if request.method == 'POST':
        form = CredentialApplicationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Credential record added successfully.')
            return redirect('credential_add')  # redirect back to form or change as needed
    else:
        form = CredentialApplicationForm()

    return render(request, 'credentials/credential_add.html', {'form': form})



def credential_list(request):
    qs = Credentials.objects.all().order_by('-id')

    # Get filter params
    location = request.GET.get('location')
    device = request.GET.get('device')
    lan_ip = request.GET.get('lan_ip')
    wan_ip = request.GET.get('wan_ip')
    url = request.GET.get('url')

    if location:
        qs = qs.filter(location=location)
    if device:
        qs = qs.filter(device__icontains=device)
    if lan_ip:
        qs = qs.filter(lan_ip__icontains=lan_ip)
    if wan_ip:
        qs = qs.filter(wan_ip__icontains=wan_ip)
    if url:
        qs = qs.filter(url__icontains=url)

    paginator = Paginator(qs, 10)  # 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'credentials': page_obj,
        'filter_location': location or '',
        'filter_device': device or '',
        'filter_lan_ip': lan_ip or '',
        'filter_wan_ip': wan_ip or '',
        'filter_url': url or '',
        'location_choices': Credentials.LOCATION_CHOICES,
    }
    return render(request, 'credentials/credential_list.html', context)


def credential_edit(request, pk=None):
    if pk:
        instance = get_object_or_404(Credentials, pk=pk)
        heading = "Edit Credential Record"
    else:
        instance = None
        heading = "Add Credential Record"

    if request.method == "POST":
        form = CredentialApplicationForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            if pk:
                messages.success(request, "Credential record updated successfully.")
            else:
                messages.success(request, "Credential record added successfully.")
            return redirect('credential_list')  # Redirect to list or change as needed
    else:
        form = CredentialApplicationForm(instance=instance)

    return render(request, "credentials/credential_add.html", {
        "form": form,
        "heading": heading,
    })


def credential_delete(request, pk):
    credential = get_object_or_404(Credentials, pk=pk)
    if request.method == "POST":
        credential.delete()
        messages.success(request, "Credential record deleted successfully.")
        return redirect('credential_list')
    # Optional: You can add confirmation template or redirect directly
    return redirect('credential_list')