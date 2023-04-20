import math
import requests
import xmltodict
import xml.etree.ElementTree as ET
import urllib.request
import yaml
import time
import os
import io
import matplotlib.pyplot as plt
import numpy as np
import json
import csv
import redis
from datetime import datetime
from datetime import timedelta
from geopy.geocoders import Nominatim
from flask import Flask, request, jsonify
from geopy.point import Point

app = Flask(__name__)

#From Homework 8 to Automatically Connect to Kubernetes
#redis_ip = os.environ.get('REDIS_IP')
#if not redi_ip:
#    raise Exception('REDIS_IP enviornment variable not sen\n')
#rd = redis.Redis(host = redis_ip, port = 6379, db = 0)

#Connect to redis without kubernetes - for development of API
rd = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

# Second redis db to store plots on so as not not mix data
# should probably make functions to catch exception errors, but that'll come later.
rd_image = redis.Redis(host='127.0.0.1', port=6379, db=1, decode_responses=True)

#Load in data 
@app.route('/data', methods = ['POST', 'GET', 'DELETE'])
def load_data():
    """
    """
    if request.method == 'POST' :
        url = "https://data.nasa.gov/api/views/mc52-syum/rows.xml?accessType=DOWNLOAD"
        response = requests.get(url)
        root = ET.fromstring(response.content)
        rows = root.findall(".//row")
        guess = root.findall("./row")
        for this in guess:
            print("guess: " ,guess)
        for item in rows:
            fb_uuid = item.get('_uuid')
            print(item)
            if fb_uuid is not None:
                item_dict = {}
                for key, value in item.items():
                    # This section adds the id, uuid, position, and address
                    if key is not None and value is not None:
                         item_dict[key] = value
                #This section adds rest of data
                altitude = item.find('altitude_km')
                if altitude is not None:
                    item_dict['altitude'] = altitude.text
                peak_brightness = item.find('date_time_peak_brightness_ut').text
                if peak_brightness is not None:
                    item_dict['peak_brightness'] = peak_brightness
                x_velocity = item.find('velocity_components_km_s_vx')
                if x_velocity is not None:
                    item_dict['x_velocity'] = x_velocity.text
                y_velocity = item.find('velocity_components_km_s_vy')
                if x_velocity is not None:
                    item_dict['y_velocity'] = y_velocity.text
                z_velocity = item.find('velocity_components_km_s_vz')
                if z_velocity is not None:
                  item_dict['z_velocity'] = z_velocity.text
                latitude = item.find('latitude_deg')
                if latitude is not None:
                    item_dict['latitude'] = latitude.text
                longitude = item.find('longitude_deg')
                if longitude is not None:
                    item_dict['longitude'] = longitude.text
                velocity = item.find('velocity_km_s')
                if velocity is not None:
                    item_dict['velocity'] = velocity.text
                radiated_energy = item.find('total_radiated_energy_j')
                if radiated_energy is not None:
                    item_dict['radiated_energy'] = radiated_energy.text
                impact_energy = item.find('calculated_total_impact_energy_kt')
                if impact_energy is not None:
                    item_dict['impact_energy'] = impact_energy.text
                #Map item_dict to unique uuid
                #rd.hset(fb_uuid, mapping = item_dict)
                #Map item_dict to a unique peak_brightness date
                rd.hset(peak_brightness, mapping = item_dict)
        return 'Fireball and Bolide data loaded into Redis.\n'

    #Return all Redis data to the user
    if request.method == 'GET' : 
        keys = rd.keys()
        output_list = []
        for key in keys:
            data = rd.hgetall(key)
            output_list.append(data)
        return jsonify(output_list)

    #Delete all data from Redis
    elif request.method == 'DELETE' :
        rd.flushdb()
        return 'Fireball and Bolide data DELETED from Redis.\n'

@app.route('/timestamp', methods = ['GET'])
def peak_brightness_timestamp():
    """
    """
    keys = rd.keys()
    data = []
    for key in keys:
        pb_date = rd.hget(key, 'peak_brightness')
        if pb_date:
            data.append(pb_date)

    return jsonify(data)

@app.route('/timestamp/<string:pb_date>', methods = ['GET'])
def value_at_pb_date(pb_date):
    """
    """
    data = rd.hgetall(pb_date)
    if not data:
        return 'No data associated with this timestamp.\n'
    return jsonify(data)

@app.route('/timestamp/<string:pb_date>/speed', methods = ['GET'])
def velocity_at_pb_date(pb_date):
    """
    """
    data = value_at_pb_date(pb_date)
    #Return only the velocity data
    if not data:
        return 'No velocity data available at this timestamp.\n'
    if rd.hget(pb_date,'x_velocity') is not None and rd.hget(pb_date,'y_velocity') is not None and rd.hget(pb_date,'z_velocity') is not None:
        val_data = {'x_velocity': rd.hget(pb_date,'x_velocity') + " [km/s]",
                       'y_velocity': rd.hget(pb_date,'y_velocity') + " [km/s]",
                       'z_velocity': rd.hget(pb_date,'z_velocity') + " [km/s]"}
    else:
        val_data = {'x_velocity': "N/A" + " [km/s]",
                    'y_velocity': "N/A" + " [km/s]",
                    'z_velocity':  "N/A" + " [km/s]"}
    return jsonify(val_data)
    

@app.route('/timestamp/<string:pb_date>/energy', methods = ['GET'])
def energy_at_pb_date(pb_date):
    """
    """
    data = value_at_pb_date(pb_date)
    if not data:
        return 'No velocity data available at this timestamp.\n'

    val_data = {'radiated_energy': rd.hget(pb_date,'radiated_energy') + " [J]",
                'calculated_impact_energy' : rd.hget(pb_date, 'impact_energy') + " [kT]"}

    return jsonify(val_data)


#EDIT THIS FOR USE IN FIREBALL_API
#Route to return latitude, longitue, altitude, and geoposition for given epoch.
@app.route('/timestamp/<string:pb_date>/location', methods = ['GET'])
def fireball_location(pb_date:str) -> dict:
    """
    Route that returns latitude, longitude, altitude, and geoposition for a given <epoch>.

    Returns:
    Dictionary containing latitude, longitude, altitude, and geoposition.
    """
    data = rd.hgetall(pb_date)
    if not data:
        return 'No position data available at this timestamp.\n'
    altitude = rd.hget(pb_date, 'altitude') #- EARTH_RADIUS already included?
    #the latitude and longitude have a 'N,S,E,W' direction on the string
    latitude = rd.hget(pb_date, 'latitude')
    longitude = rd.hget(pb_date, 'longitude')

    lat_deg = float(latitude[:-1]) 
    lat_dir = -1 if latitude[-1] == 'S' else 1
    long_deg = float(longitude[:-1])
    long_dir = -1 if longitude[-1] == 'W' else 1
    
    latitude = lat_deg * lat_dir
    longitude = long_deg * long_dir

    geolocator = Nominatim(user_agent="fireball_api") #IDK what to change this to
    location = geolocator.reverse((latitude,longitude), zoom=15, language='en')

    if location is None:
        geoposition = "Geoposition is not available at this timestamp.\n" 
    else:
        geoposition = location.address
        address = location.raw['address']
        country = address.get('country', '')
        county = address.get('county', '')
        region = address.get('region', '')
        state = address.get('state', '')
        district = address.get('suburb') or address.get('city_district')
    velocity = velocity_at_pb_date(pb_date)
    if rd.hget(pb_date, 'x_velocity') is None: 
        x_velocity = "N/A"
    else: x_velocity = rd.hget(pb_date, 'x_velocity')
    if rd.hget(pb_date, 'z_velocity') is None: y_velocity = "N/A"
    else: y_velocity = rd.hget(pb_date, 'y_velocity')
    if rd.hget(pb_date, 'z_velocity') is None: z_velocity = "N/A"
    else: z_velocity = rd.hget(pb_date, 'z_velocity')
    pos_unit = "km"
    #Geoposition problem due to latitude & longitude?
    print(velocity)
    location_dict = {
            'latitude' : latitude,
            'longitude' :longitude,
            'pos_unit' : pos_unit,
            'altitude': altitude,
            'x_velocity' :  x_velocity + ' [km/s]',
            'y_velocity' : y_velocity + ' [km/s]',
            'z_velocity' : z_velocity + ' [km/s]',
            #'address' : address ,
            #'geopos':  geoposition,
            'geo_country' : country,
            'county' : county,
            'district' : district,
            'region' : region,
            'state': state
    }

    return location_dict

@app.route('/help', methods = ['GET'])
def help():
    """
    """
    output = 'Available routs and methods: \n'

    for route in app.url_map.iter_rules():
        if route.endpoint != 'static':
            methods = ','.join(route.methods)
            output += f'{route.rule} [{methods}]\n'
            if route.endpoint:
                func = app.view_functions[route.endpoint]
                output += f'{func.__doc__}\n\n'
    return output

@app.route('/graph', methods = ['GET','POST','DELETE'])
def create_graph():
    """
    """
    
    if request.method == 'DELETE':
        rd_image.flushdb()
        return 'The graphs have been removed from the redis database.\n'

    # Should be working?? Not 100%
    elif request.method == 'POST':
        if (len(rd.keys()) == 0):
            return 'No data is available. Please Post the data.'
        else:
            keys = rd.keys()
            for key in keys:
                if rd.hget(key, 'radiated_energy') is not None and rd.hget(key, 'impact_energy') is not None:
                    # Need to ensure array sizes are the same.
                    energy_radiated = np.asarray([rd.hget(key, 'radiated_energy')])
                    ttl_impact_energy = np.asarray([rd.hget(key, 'impact_energy')])

            plt.scatter(energy_radiated, ttl_impact_energy)
            plt.xlabel('Total Energy Radiated')
            plt.ylabel('Total Impact Energy')

            buf = io.BytesIO()
            plt.savefig(buf, format = 'jpg')
            buf.seek(0)

            rd_image.set('image',buf.getvalue())

            return 'Image has been posted'
    
    # posting/getting are identical to my hw8, which was working. Should work once POST does.
    elif request.method == 'GET':
        image = rd_image.get()
        buf = io.BytesIO(image)
        buf.seek(0)

        existing_images = rd_image.keys() == 0

        file_name = f'image{existing_images}.jpg'

        return send_file(buf, mimetype = 'image/jpg')



    else:
        return 'The method used is not supported. Please use GET, DELETE, or POST.'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    #config = get_config()
    #if config.get('debug', True):
    #    app.run(debug=True, host='0.0.0.0')
    #else:
    #    app.run(host = '0.0.0.0')
