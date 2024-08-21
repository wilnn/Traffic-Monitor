import requests, os
from dotenv import load_dotenv

load_dotenv()

def geocodingService(city, state, country):
    # Define your API key and the city/state
    api_key = os.getenv('GOOGLEAPIKEY')

    query = f'{city}, {state}, {country}'

    # Make the API request
    url = os.getenv('GEOCODINGURL')
    params = {
        'address': query,
        'key': api_key
    }
    response = requests.get(url, params=params)
    data = response.json()

    # Extract the bounding box from the response
    if data['status'] == 'OK' and len(data['results']) > 0:
        result = data['results'][0]
        viewport = result['geometry']['viewport']
        northeast = viewport['northeast']
        southwest = viewport['southwest']
        
        #print(f"Northeast Corner: Latitude: {northeast['lat']}, Longitude: {northeast['lng']}")
        #print(f"Southwest Corner: Latitude: {southwest['lat']}, Longitude: {southwest['lng']}")
        return northeast, southwest
    else:
        #print("City not found or error in API request.")
        return 'ERROR2'

#geocodingService('Boston', 'Massachusetts', 'United State')

def trafficIncidentService(topRight, bottomLeft):
    url = os.getenv('TRAFFICINCIDENTURL')
    bbox = f"{bottomLeft['lng']}, {bottomLeft['lat']}, {topRight['lng']}, {topRight['lat']}"
    params = {
        "key": os.getenv('TOMTOMAPIKEY'),
        "bbox": bbox,
        #"fields": "id,geometry,properties",
        #"categories": "JAM,ROADWORK",
        'language': 'en-US'
    }
    
    response = requests.get(url, params=params)