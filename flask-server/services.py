import requests, os
from dotenv import load_dotenv
import json
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
    if response.status_code != 200:
        return f'Can not make request to Google API. ERROR: {response.status_code}'
    data = response.json()

    # Extract the bounding box from the response
    if data['status'] == 'OK' and len(data['results']) > 0:
        result = data['results'][0]
        viewport = result['geometry']['viewport']
        northeast = viewport['northeast']
        southwest = viewport['southwest']
        
        print(f"Northeast Corner: Latitude: {northeast['lat']}, Longitude: {northeast['lng']}")
        print(f"Southwest Corner: Latitude: {southwest['lat']}, Longitude: {southwest['lng']}")
        return northeast, southwest
    else:
        #print("City not found or error in API request.")
        return 'ERROR2'

def trafficIncidentService(topRight, bottomLeft):
    url = os.getenv('TRAFFICINCIDENTURL')
    bbox = f"{bottomLeft['lng']}, {bottomLeft['lat']}, {topRight['lng']}, {topRight['lat']}"
    #field = "{incidents{type,geometry{type,coordinates},properties{id,iconCategory,magnitudeOfDelay,events{description,code,iconCategory},startTime,endTime,from,to,length,delay,roadNumbers,timeValidity,probabilityOfOccurrence,numberOfReports}}}"
    field = "{incidents{type,properties{id,iconCategory,magnitudeOfDelay,events{description,code,iconCategory},startTime,endTime,from,to,length,delay,roadNumbers,timeValidity,probabilityOfOccurrence,numberOfReports}}}"

    params = {
        "key": os.getenv('TOMTOMAPIKEY'),
        "bbox": bbox,
        "fields": field,
        #"categories": "JAM,ROADWORK",
        'language': 'en-US'
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return f'Can not make request TomTom API. ERROR: {response.status_code}'
    data = response.json()
    
    #print(json.dumps(data, indent=4))

