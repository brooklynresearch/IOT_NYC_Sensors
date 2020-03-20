# IOTPOC
Internet of Things Platform Proof of Concept

## Features and Usage
The web app consists of 3 pages:
  * Landing page `http://<server-ip>:8000/`
  * Map view page `http://<server-ip>:8000/map`
  * Plot view page `http://<server-ip>:8000/plot`

The landing page is the entry point to the app and provides links to the map and plot pages.
![landing_img]

The map view displays a map of NYC and a menu of all the sensors, categorized by type. Clicking a sensor will
add a marker on the map. Clicking 'Select All' will add all sensors of that type to the map. Clicking on a
marker will open a popup box with information about the sensor
and a plot of its latest readings, along with controls to select the time range of the plot (1 week, 1 month, etc.).
![map_img]

The plot view is a cartesian graph with the same sensor menu as the map view. This view allows a user to plot data
from multiple sensors at once and apply filters for time span and min and max values. For example, a user can plot
all air quality readings above 25 along with all sound level readings above 70 within a certain time window. There is
also a button on this page to generate a table of the current plot data. From the table, a user can export the
graph data in CSV format.
![plot_img]

There are links to view the current sensor selections on the alternate view, map from plot and vice-versa.

## Management
When logged into AWS with a MOCTO account, the server instance can be managed here:
  * [https://us-east-2.console.aws.amazon.com/ec2/home?region=us-east-2#Instances:sort=desc:statusChecks]

For shell access click 'connect' on the dashboard page above for instructions

There is also an admin dashboard for the site itself at `http://18.220.143.195:8000/admin` (see credentials doc).
    This page can be used to create or update admin users and update sensor info.

## Creating a New Instance
* Clone this repository
* Create a postgreSQL database named 'iotpoc'
* Create a postgreSQL user 'iotpoc' with superuser role and password of your choice
* Create and activate a python virtual environment for the project
* In the project directory, run `pip install -r requirements.txt` to install the dependencies
* On startup, the server looks for 3 environment variables
  * 'DJANGO_SECRET_KEY' (see credentials doc)
  * 'DJANGO_DEBUG_MODE' (set 'true' to run local dev server)
  * 'IOTPOC_DB_PASSWORD' (the postgres password created above)
  These can be defined in the python virtual environment bin/activate file for convenience
* Create database migrations
  * `python manage.py makemigrations`
* Apply migrations
  * `python manage.py migrate`
* Run the development server
  * `python manage.py runserver`
* Test it
  * `http://localhost:8000/`
* To use admin dashboard on a development server
  * `python manage.py createsuperuser`
  * create username and password for admin
  * run server and go to `http://localhost:8000/admin`
  
## Ingesting Data
New sensor data is added to the database with a set of scripts found in the scripts folder. Each script is named
`store_<sensor-type>_data.py`. The scripts for air, traffic, and sound readings all grab data from
web APIs. These scripts are set to run every 15 mins via cron. They can be run at any time to gather new data.

The Belmont ave Nightlight pedestrian sensors work differently. These sensors send
their readings directly to a MQTT broker running on the server instance. The `store_pedcount_readings.py`
script runs as a background service and continuously listens for new data sent to the broker.

As of 9/17 the traffic data is split by traffic classification for each sensor. So each physical sensor may be
respresented as multiple sensors within the app. The current sensor is only counting
pedestrians, listed as 'Brooklyn Bridge Pedestrians'. Older data for this sensor is still listed under the original name
'Brooklyn Bridge'. The 39th street sensor will also be counting vehicles and these counts will be listed like
'39th St Cars', '39th St Buses' etc.

Once the new traffic sensor is installed, the only change needed will be the API_QUERY string
in `store_traffic_readings.py`

## Dev Info
### API
* The API provides an interface for adding and retrieving sensor data
There is an endpoint for each sensor type:
  * `api/air_data`
  * `api/sound_data`
  * `api/pedcount_data`
  * `api/traffic_data`

Each of these supports both `GET` and `POST` requests.
  
`GET` requests all return JSON lists of sensors and readings.<br>
Example response: `{"readings": [...], "sensors": [...]}`
  
Each reading is associated with its sensor via its sensor_id field
  
There are 3 ways to query sensor data:
  * count: returns all sensors of endpoint type and their <count> most recent readings
    * Ex `/api/air_data?count=20` to get each air sensor with its 20 most recent readings
  * days: returns all sensors of endpoint type and their readings from the last <days> days
    * Ex `/api/air_data?days=5` to get each air sensor with its readings from last 5 days
  * start and end times: returns all sensors of endpoint type and their readings between <start> and <end> timestamps
    * Ex `/api/air_data?start=2019-09-09T20:29:57.661Z&end=2019-09-16T20:29:57.661Z` to get each air sensor 
    with its readings between the given timestamps
    
`POST` requests are meant to be used by the scripts that gather the associated sensor data. The API expects a
   JSON list of readings of the endpoint type in the request body. The format of the readings themselves depends
   on the type.
    
There is also an endpoint to `GET` a list of sensor types in the database.<br>
This list can be used to generate data queries for each sensor type.
  
  * Route: `api/sensor_types`
  * Example response: `{"sensor_types": ["air", "pedcount", "sound", "traffic"]}`

### Database Schema
```text
table api_sensor {
    external_id: string -- id of the sensor in its original API
    name: string -- display name of the sensor
    owner: string -- dept which owns the sensor
    contact: string -- contact info for owner 
    sensor_type: string -- one of ['air', 'sound', 'pedcount', 'traffic']
    description: string -- not used
    data_field: string -- field name of the reading to use (i.e PM_25 for an air sensor)
    latitude: float
    longitude: float
    latest_reading: datetime -- time of most recent reading
}

table api_<type-name>reading { -- one table for each type. i.e. api_soundreading
    sensor_id: primary-key -- id from table api_sensor
    id: integer -- id number of the reading
    timestamp: datetime -- time of this reading
    <data fields specific to each sensor...> -- data_field of the sensor gives field to use
}
```
### Software and Library Versions
  * Server OS:
    * Ubuntu 18.04.3 LTS
  * Backend:
    * Python 3.6.7
    * Django 2.1.5
    * PostgreSQL 9.5.7
    * nginx 1.14.0
    * mosquitto 1.4.15
  * Frontend (included in this repo):
    * jQuery 3.4.1
    * jQuery UI 1.12.1
    * plotly.js 1.49.4
    * leaflet.js 1.4.0

## Extending the Proof-of-Concept
The app was designed around a specific set of sensors. Further development would involve redisigning the API to
create a generalized standard interface for adding and requesting sensor data of any kind. This would allow for
dynamically adding new sensor categories. The frontend code would likewise be updated to display any kind of sensor
data.

[landing_img]: iotpoc-landing.png
[map_img]: iotpoc-map.png
[plot_img]: iotpoc-plot4.png
