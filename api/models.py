from django.db import models

# Create your models here.

class Sensor(models.Model):
    external_id = models.IntegerField()
    name = models.CharField(max_length=100, default="")
    display_name = models.CharField(max_length=100, default="")
    owner = models.CharField(max_length=100, default="")
    contact = models.CharField(max_length=100, default="")
    sensor_type = models.CharField(max_length=100)
    description = models.CharField(max_length=100, default="")
    data_field = models.CharField(max_length=100, default="")
    latitude = models.FloatField()
    longitude = models.FloatField()
    latest_reading = models.DateTimeField()


class AirQualityReading(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name="air_readings")
    timestamp = models.DateTimeField()
    roll_PM25 = models.FloatField()
    current_PM25 = models.FloatField()
    site = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    bldgarea_c = models.CharField(max_length=100)
    traffic_cl = models.CharField(max_length=100)

class SoundReading(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name="sound_readings")
    timestamp = models.DateTimeField()
    davg = models.FloatField()
    dmin = models.FloatField()
    dmax = models.FloatField()
    d_l10 = models.FloatField()
    d_l50 = models.FloatField()
    d_l90 = models.FloatField()


class PedCountReading(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name="pedcount_readings")
    timestamp = models.DateTimeField()
    count = models.IntegerField()

class TrafficReading(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name="traffic_readings")
    timestamp = models.DateTimeField()
    count = models.IntegerField()
