from django.urls import path

from . import views

app_name = 'visits'

urlpatterns = [
    path('', views.visit_request_view, name='visit_request'),
    path('exito/', views.visit_request_success, name='visit_request_success'),
    path('panel/', views.company_dashboard, name='company_dashboard'),
    path('asignar/<int:pk>/', views.assign_gardener, name='assign_gardener'),
    path(
        'confirmar/<uuid:token>/',
        views.visit_confirm,
        name='visit_confirm',
    ),
    path(
        'cancelar/<uuid:token>/',
        views.visit_cancel,
        name='visit_cancel',
    ),
    path('logout/', views.logout_view, name='logout'),
    path('documentacion/', views.documentation, name='documentation'),
]
