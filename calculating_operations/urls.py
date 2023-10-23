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
from django.urls import include, path
from rest_framework import routers

from app.migration import views

router = routers.DefaultRouter()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path(r"operations/", views.get_calculations_list, name='calculations_list'),
    path(r'operations/<int:pk>/', views.get_calculations_detailed, name='calculation_type_detailed'),
    path(r'operations/create/', views.create_calculation_type, name='create_calculation_type'),
    path(r'operations/<int:pk>/edit/', views.change_calculation_type_data, name='change_calculation_type_data'),
    path(r'operations/<int:pk>/delete/', views.delete_calculation, name='delete_calculation_type'),
    path(r'operations/<int:pk>/add/', views.add_calculation_type, name='add_calculation_type'),

    path(r"applications/", views.get_applications_list, name='applications_list'),
    path(r"applications/<int:pk>/", views.get_application_detailed, name='get_application_detailed'),
    path(r'applications/<int:pk>/change_inputs/', views.change_inputs_application, name='change_inputs_application'),
    path(r'applications/<int:application_id>/operations_delete/<int:calculation_id>/', views.delete_calculation_from_application,name='delete_calculation_from_application'),
    path(r'applications/<int:application_id>/delete/', views.delete_application_for_calculation, name='delete_application_for_calculation'),
    path(r'applications/<int:pk>/change_status/moderator/', views.put_applications_moderator, name='application_status_by_moderator'),
    path(r'applications/<int:pk>/change_status/client/', views.put_applications_client, name='application_status_by_client'),
]
