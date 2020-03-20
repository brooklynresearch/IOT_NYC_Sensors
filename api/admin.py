from django.contrib import admin

# Register your models here.
from .models import Sensor

class SensorAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'sensor_type', 'data_field', 'owner', 'external_id', 'latitude', 'longitude', 'latest_reading')
    list_filter = ['sensor_type', 'owner', 'latest_reading']

admin.site.register(Sensor, SensorAdmin)
