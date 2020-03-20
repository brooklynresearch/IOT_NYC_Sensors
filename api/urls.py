from django.urls import path

from . import views

urlpatterns = [
    path('air_data', views.air_data, name='air_data'),
    path('sound_data', views.sound_data, name='sound_data'),
    path('pedcount_data', views.pedcount_data, name='pedcount_data'),
    path('traffic_data', views.traffic_data, name='traffic_data'),
    path('sensor_types', views.sensor_types, name='sensor_types')
]
