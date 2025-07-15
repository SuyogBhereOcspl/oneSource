
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('', include('HR.urls')),
    path('', include('STORE.urls')),
    path('', include('PRODUCTION.urls')),
    path('', include('EHS.urls')),
    path('', include('ETP.urls')),
    path('', include('CANTEEN.urls')),
    path('', include('UTILITY.urls')),
    path('', include('QC.urls')),
    path('', include('CREDENTIALS.urls')),
    path('', include('CONTRACT.urls')),
    path('', include('HR_BUDGET.urls')),
    path('', include('R_and_D.urls')),
    path("select2/", include("django_select2.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
]

