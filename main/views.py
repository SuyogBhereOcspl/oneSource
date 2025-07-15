import logging
from django.shortcuts import render,HttpResponseRedirect, redirect
from django.contrib.auth.decorators import login_required
from django.contrib .auth import authenticate,login,logout
from django.contrib.auth.forms import AuthenticationForm
from main.forms import LoginForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Initialize logger
logger = logging.getLogger('custom_logger')

# Create your views here.
#index page
@login_required
def indexpage(request):
    try:
        if request.user.is_authenticated:
            user_groups = request.user.groups.values_list('name', flat=True)
            is_superuser = request.user.is_superuser
            show_admin_panel = is_superuser or (request.user.is_staff and request.user.is_active)

            logger.info(f"User '{request.user.username}' accessed index page.")
            return render(request, 'main/index.html', locals())
        else:
            logger.warning("Unauthorized attempt to access index page.")
            return HttpResponseRedirect("/")
        
    except Exception as e:
        logger.exception(f"Error in indexpage view by user: {request.user}")
        messages.error(request, "An unexpected error occurred on the dashboard.")
        return HttpResponseRedirect("/")


def LoginPage(request):
    try:
        if request.user.is_authenticated:
            logger.info(f"User '{request.user.username}' tried to access login page but is already authenticated.")
            return redirect('/indexpage/')

        if request.method == "POST":
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                uname = form.cleaned_data['username']
                upass = form.cleaned_data['password']
                user = authenticate(username=uname, password=upass)
                if user is not None:
                    login(request, user)
                    logger.info(f"User '{uname}' logged in successfully.")
                    messages.success(request, 'Logged in successfully!')
                    return redirect('/indexpage/')
                else:
                    logger.warning(f"Failed login attempt for username '{uname}'.")
                    messages.error(request, 'Invalid username or password!')
            else:
                logger.warning("Invalid login form submitted.")
        else:
            form = AuthenticationForm()

        return render(request, 'main/login.html', {'form': form})
    except Exception as e:
        logger.exception("Error occurred during login")
        messages.error(request, "An unexpected error occurred during login.")
        return redirect('/')



#logout
@login_required
def User_logout(request):
    try:
        if request.user.is_authenticated:
            logger.info(f"User '{request.user.username}' logged out.")
            logout(request)
            messages.success(request, 'Logout successfully !!')
            return HttpResponseRedirect("/")
        else:
            logger.warning("Unauthenticated logout attempt.")
            return HttpResponseRedirect("/")
    except Exception as e:
        logger.exception(f"Error occurred during logout by user: {request.user}")
        messages.error(request, "An error occurred during logout.")
        return HttpResponseRedirect("/")


def Signup_Page(request):
    logger.info(f"User '{request.user.username}' attempted to access signup page.")
    messages.success(request, 'Contact to IT Adminitstrator!!')
    return HttpResponseRedirect("/")


# auth/login?next=%2F