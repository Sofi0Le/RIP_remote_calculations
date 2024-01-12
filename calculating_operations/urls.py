"""
URL configuration for bmstu_lab project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from rest_framework import permissions
from django.urls import include, path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import routers

from app.migration import views

router = routers.DefaultRouter()

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path(r'api/users/registration/', views.registration, name='registration'),
    path(r'api/users/login/', views.login_view, name='login'),
    path(r'api/users/logout/', views.logout_view, name='logout'),
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path(r"api/operations/", views.get_calculations_list, name='calculations_list'),
    path(r'api/operations/<int:pk>/', views.get_calculations_detailed, name='calculation_type_detailed'),
    path(r'api/operations/create/', views.create_calculation_type, name='create_calculation_type'),
    path(r'api/operations/<int:pk>/edit/', views.change_calculation_type_data, name='change_calculation_type_data'),
    path(r'api/operations/<int:pk>/delete/', views.delete_calculation, name='delete_calculation_type'),
    path(r'api/operations/<int:pk>/add/', views.add_calculation_type, name='add_calculation_type'),
    path(r'api/operations/upload_photo/', views.calculation_upload_photo, name='upload_photo'),
    #path(r'api/operations/<int:pk>/edit_im/', views.change_calculation_image, name='change_calculation_image'),

    path(r"api/applications/", views.get_applications_list, name='applications_list'),
    path(r"api/applications/<int:pk>/", views.get_application_detailed, name='get_application_detailed'),
    path(r'api/applications/<int:pk>/change_inputs/', views.change_inputs_application, name='change_inputs_application'),
    path(r'api/applications/<int:application_id>/delete/', views.delete_application_for_calculation, name='delete_application_for_calculation'),
    path(r'api/applications/<int:pk>/change_status/moderator/', views.put_applications_moderator, name='application_status_by_moderator'),
    path(r'api/applications/<int:pk>/change_status/client/', views.put_applications_client, name='application_status_by_client'),

    path(r'api/applications/write_result_calculating/', views.write_calculating_result, name='write_result_calculating'),

    path(r'api/applications_calculations/<int:pk>/<int:calculation_id>/', views.edit_result_applications_calculations, name='edit_result_applications_calculations'),
    path(r'api/applications_calculations/<int:application_id>/operations_delete/<int:calculation_id>/', views.delete_calculation_from_application,name='delete_calculation_from_application'),
]
