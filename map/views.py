from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
import json

# Create your views here.
@cache_control(max_age=3600)
def index(request):
    sensor_list = request.GET.getlist('sensors', [])
    context = {'sensorIdList': str(sensor_list)}
    template = loader.get_template('map/index.html')
    return HttpResponse(template.render(context, request))
