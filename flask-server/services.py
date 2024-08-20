import requests, os
from dotenv import load_dotenv

load_dotenv()

def geocodingService(city, state, country):
    # Define your API key and the city/state
    api_key = os.getenv('GOOGLEAPIKEY')

    query = f'{city}, {state}, {country}'

    # Make the API request
    url = f'https://maps.googleapis.com/maps/api/geocode/json'
    params = {
        'address': query,
        'key': api_key
    }
    response = requests.get(url, params=params)
    data = response.json()

