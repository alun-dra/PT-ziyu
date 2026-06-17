from django.contrib import admin

from .models import Gardener, ServiceType, VisitRequest


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    list_editable = ('is_active',)


@admin.register(Gardener)
class GardenerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone', 'email', 'specialty', 'is_active')
    list_filter = ('is_active', 'specialty')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    list_editable = ('is_active',)


@admin.register(VisitRequest)
class VisitRequestAdmin(admin.ModelAdmin):
    list_display = (
        'client_name',
        'service_type',
        'status',
        'gardener',
        'address',
        'preferred_date',
        'created_at',
    )
    list_filter = ('status', 'service_type', 'gardener', 'created_at')
    search_fields = ('client_name', 'client_email', 'address')
    list_editable = ('status', 'gardener')
    readonly_fields = ('confirmation_token', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Datos del Cliente', {
            'fields': ('client_name', 'client_email', 'client_phone'),
        }),
        ('Ubicación', {
            'fields': ('address', 'latitude', 'longitude'),
        }),
        ('Servicio', {
            'fields': ('service_type', 'garden_area_sqm'),
        }),
        ('Agenda', {
            'fields': ('preferred_date', 'preferred_time_start', 'preferred_time_end'),
        }),
        ('Notas', {
            'fields': ('notes',),
        }),
        ('Estado', {
            'fields': ('status', 'gardener'),
        }),
        ('Sistema', {
            'fields': ('confirmation_token', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
