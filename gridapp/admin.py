from django.contrib import admin
from .models import Staff, ServerRoomEntry, FaultReport, FieldActivity
from django.http import HttpResponse
import csv


@admin.action(description='Suspend selected staff')
def suspend_staff(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description='Export selected to CSV')
def export_as_csv(modeladmin, request, queryset):
    meta = modeladmin.model._meta
    field_names = [f.name for f in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={meta}.csv'
    writer = csv.writer(response)
    writer.writerow(field_names)
    for obj in queryset:
        writer.writerow([getattr(obj, f) for f in field_names])
    return response


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_active')
    actions = [suspend_staff, export_as_csv]


@admin.register(ServerRoomEntry)
class ServerRoomEntryAdmin(admin.ModelAdmin):
    list_display = ('staff', 'date', 'time_in', 'time_out', 'supervisor')
    list_filter = ('date', 'staff')
    actions = [export_as_csv]


@admin.register(FaultReport)
class FaultReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_reported', 'reported_by', 'location', 'status')
    list_filter = ('status', 'date_reported')
    actions = [export_as_csv]


@admin.register(FieldActivity)
class FieldActivityAdmin(admin.ModelAdmin):
    list_display = ('staff', 'substation', 'date', 'time_out', 'time_returned')
    list_filter = ('date', 'substation')
    actions = [export_as_csv]
