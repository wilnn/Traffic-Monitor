##########

# this module is the server of the website. It is hosted on the Google Cloud App Engine

##########


from flask import Flask, request, jsonify
import uuid
import mysql.connector
from flask_cors import CORS
import services
from dotenv import load_dotenv
from datetime import timedelta, timezone
import smtplib, datetime, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import TooManyRequests
#import geocoder
#from timezonefinder import TimezoneFinder

app = Flask(__name__)
# enable CORS. Only allow request from "https://traffic-monitor.pages.dev"
cors = CORS(app, resources={r"/*": {"origins": "https://traffic-monitor.pages.dev"}})

load_dotenv()

def testEmail(email):
    message = MIMEMultipart()
    message["From"] = os.getenv('SENDER_EMAIL')
    message["To"] = email
    message["Subject"] = 'Test Email'
    body = "This email is to verify that the given email is correct, and you can start receiving emails regarding traffic incidents from now on."
    message.attach(MIMEText(body, "plain"))

    # Establish a connection to the SMTP server
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            # Start the TLS connection
            server.starttls()

            # Login to your Gmail account
            server.login(os.getenv('SENDER_EMAIL'), os.getenv('EMAIL_PASSWORD'))
            # Send the email
            server.sendmail(os.getenv('SENDER_EMAIL'), email, message.as_string())
    except Exception as e:
        print('error sending email: '+ str(e))
        return -1
    return 0

def data():
    #force=True to skip content type requirement
    data = request.get_json()

    conn = mysql.connector.connect(host=os.getenv('HOST'), database=os.getenv('DBNAME'), user=os.getenv('USER'), 
                        password=os.getenv('PASSWORD'), port=os.getenv('PORTT'))
    
    if not conn.is_connected():
        return {"value":'ERROR0'}
    cur = conn.cursor()

    # check database storage
    query = """
        SELECT 
            table_schema AS "TrafficMonitor_rememberwe",
            SUM(data_length + index_length) / 1024 / 1024 AS "database size in MB",
            SUM(data_free) / 1024 / 1024 AS "free space in MB"
        FROM 
            information_schema.TABLES
        GROUP BY 
            table_schema;
        """

    # Execute the query
    cur.execute(query)

    # Fetch all results
    results = cur.fetchall()
    # the current maximum storage is 10 MB. If the database size is >= 9.8 MB, will not add new entries
    if results[2][1] >= 9.8:
        return {'value':'ERROR4'}
    
    # get the bounding box for the given location. also test that location. It will not work if the location is more than 10,000km^2
    northeast, southwest = services.geocodingService(data['city'], data['state'], data['country'])
    coordinate = f"{northeast['lng']},{northeast['lat']},{southwest['lng']},{southwest['lat']}"
    if northeast == 'ERROR2':
        return {"value":'ERROR2'}

    data2 = services.trafficIncidentService(northeast, southwest)
    if isinstance(data2, str) and 'Can not make request' in data2:
        return {"value":'ERROR3'}

    #test the given email
    status = testEmail(data['clientEmail'])
    if status == -1:
        return {'value': 'ERROR1'}

    #get not timezone specific time
    notTimeZoneAware = datetime.datetime.now(tz=datetime.UTC)

    #turn not timezone aware object into naive 
    notTimeZoneAware2 = notTimeZoneAware.astimezone(timezone.utc).replace(tzinfo=None)
    newTime = notTimeZoneAware2 + timedelta(minutes=int(data['time']))

    id = str(uuid.uuid4())
    id = id[len(id)-6:]

    cur.execute('''CREATE TABLE IF NOT EXISTS data (
                 ID varchar(7) PRIMARY KEY,
                 city varchar(200),
                 state varchar(100),
                 country varchar(100),
                 coordinate varchar(300),
                 email varchar(320),
                 timeInterval int,
                 time DATETIME,
                 next_run DATETIME,
                 incidentID varchar(10000))''')
    
    insertQuery ='''INSERT INTO data (ID, city, state, country, coordinate, email, timeInterval, time, next_run) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'''
    value = (id, data['city'], data['state'], data['country'], coordinate, data['clientEmail'], data['time'], notTimeZoneAware2, newTime)
    #use place holder method to avoid SQL injecion
    cur.execute(insertQuery, value)
    conn.commit()
    conn.close()
    cur.close()
    return {'value': 'ok'}

def unregister():
    data = request.get_json()

    conn = mysql.connector.connect(host=os.getenv('HOST'), database=os.getenv('DBNAME'), user=os.getenv('USER'), 
                        password=os.getenv('PASSWORD'), port=os.getenv('PORTT'))
    if not conn.is_connected():
        return {"value":'ERROR0'}
    cur = conn.cursor()
    query = '''DELETE FROM data WHERE email = %s'''
    value=[data['clientEmail']]
    cur.execute(query, value)
    conn.commit()
    #cur.rowcount return the number of row affected by the last query
    if not cur.rowcount:
        conn.close()
        cur.close()
        return {'value':"Email does not exist in the database. Please check the entered email."}
    else:
        conn.close()
        cur.close()
        return {'value':"Unregisted successfully"}
    

if __name__ == "__main__":
    app.run(debug=True)