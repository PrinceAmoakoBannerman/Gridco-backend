"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from . import auth_views
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/server-room/', views.server_room),
    path('api/server-room-visitors/', views.server_room_visitors),
    path('api/fault-reports/', views.fault_reports),
    path('api/faults/<int:pk>/', views.fault_detail),
    path('api/field-activities/', views.field_activities),
    path('api/dashboard/', views.dashboard),
    path('api/activity-reports/', views.activity_reports),
    # Export endpoints
    path('api/export/field-activities/csv/', views.export_field_activities_csv),
    path('api/export/fault-reports/csv/', views.export_faults_csv),
    path('api/export/activity-reports/weekly/', views.export_activity_reports_weekly_csv),
    path('api/export/activity-reports/monthly/', views.export_activity_reports_monthly_csv),
    # Authentication (JWT)
    path('api/auth/token/', auth_views.EmailOrUsernameTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/user/', auth_views.current_user),
    path('api/auth/lookup/', auth_views.lookup_user_by_email),
        path('api/auth/set-password/', auth_views.set_initial_password),
    path('api/daily-records/', views.daily_records),
    path('api/export/daily-records/csv/', views.export_daily_records_csv),
    # Feedback endpoints
    path('api/fault-feedbacks/', views.fault_feedback),
    path('api/fault-feedbacks/<int:fault_id>/', views.get_fault_feedbacks),
    # Catch-all for React Router - must be last
    re_path(r'^(?!api/).*$', views.serve_index_html),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files in production
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
