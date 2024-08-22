from flask import Flask, request
import uuid
from flask_cors import CORS
import services
from dotenv import load_dotenv
from datetime import timedelta, timezone
import smtplib, datetime, os, psycopg2
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
#import geocoder
#from timezonefinder import TimezoneFinder

app = Flask(__name__)
CORS(app)

load_dotenv()

def testEmail(email):
    message = MIMEMultipart()
    message["From"] = os.getenv('SENDER_EMAIL')
    message["To"] = email
    message["Subject"] = 'Test Email'
    body = "This email is to verify that the given email is correct, and you can start receiving emails regarding content changes from now on."
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
    

@app.route("/data", methods=['POST'])
def data():
    #force=True to skip content type requirement
    data = request.get_json()

    #handle timezone specific to user
    '''
    # Get the user's IP address from the request
    user_ip = request.remote_addr
    #will not work on local host since the ip address is a loop back ip address. Can not find lattitude and longtitude from it 
    info = geocoder.ipinfo(user_ip)
    # Use timezonefinder to get the timezone based on the location
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=info.latlng[1], lat=info.latlng[0])
    print(timezone_str)'''

    #test given email
    status = testEmail(data['clientEmail'])
    if status == -1:
        return {'value': 'ERROR1'}
    
    # get the bounding box for the given location. also test that location
    northeast, southwest = services.geocodingService(data['city'], data['state'], data['country'])
    coordinate = f"{northeast['lng']},{northeast['lat']},{southwest['lng']},{southwest['lat']}"
    if northeast == 'ERROR2':
        return {"value":'ERROR2'}
    

    
    #get not timezone specific time
    notTimeZoneAware = datetime.datetime.now(tz=datetime.UTC)

    #turn not timezone aware object into naive 
    notTimeZoneAware2 = notTimeZoneAware.astimezone(timezone.utc).replace(tzinfo=None)
    newTime = notTimeZoneAware2 + timedelta(minutes=int(data['time']))

    id = uuid.uuid4()
    id = id[len(id)-6:]

    conn = psycopg2.connect(host=os.getenv('HOST'), dbname=os.getenv('DBNAME'), user='postgres', 
                        password=os.getenv('PASSWORD'), port=os.getenv('PORT'))
    cur = conn.cursor()

    # create a table if not exist. url is the given url, email is given email,
    # interval is given time interval, time is when it is submitted by user,
    #next_run is when the next run start, id is the set of ids to be used to find the same element 
    #again when running again to find the changes, tag is the set of tags of the selected text 
    #which will be used to compare with run again to find differences
    cur.execute('''CREATE TABLE IF NOT EXISTS data (
                 ID varchar(7)
                 city varchar(200),
                 state varchar(100),
                 country varchar(100),
                 coordinate varchar(300)
                 email varchar(320),
                 interval int,
                 time TIMESTAMP PRIMARY KEY,
                 next_run timestamp without time zone,
                 incidentID varchar(10000)''')
    
    insertQuery ='''INSERT INTO data (city, state, country, coordinate, email, interval, time, next_run) VALUES (%s, %s, %s, %s, %s)'''
    value = (id, data['city'], data['state'], data['country'], coordinate, data['clientEmail'], data['time'], notTimeZoneAware2, newTime)
    #use place holder method to avoid SQL injecion
    cur.execute(insertQuery, value)
    conn.commit()
    conn.close()
    cur.close()

@app.route("/tags", methods=['POST'])
def tags():
    data = request.get_json()
    print(data)

    tags = getTagsByIDs(data['idss'])
    with open("../viewpage/viewpage.html", 'w', encoding="utf-8") as file:
        file.write('')
    
    conn = psycopg2.connect(host=os.getenv('HOST'), dbname=os.getenv('DBNAME'), user='postgres', 
                        password=os.getenv('PASSWORD'), port=os.getenv('PORT'))
    cur = conn.cursor()
    #select all row from the data table that is sorted in descending order by value in time column and then limit to 1 row(first row)(row with highest time stamp value)
    #ORDER BY will not sort the table permanently
    updateQuery= '''
    WITH LastRow AS (
        SELECT *
        FROM data
        ORDER BY time DESC
        LIMIT 1
    )
    UPDATE data
    SET id = %s,
        tag = %s
    FROM LastRow
    WHERE data.time = LastRow.time
'''
    value = (data['idss'], tags)
    cur.execute(updateQuery, value)
    conn.commit()
    conn.close()
    cur.close()

    return {}

@app.route("/unregister", methods=['POST'])
def unregister():
    data = request.get_json()

    conn = psycopg2.connect(host=os.getenv('HOST'), dbname=os.getenv('DBNAME'), user='postgres', 
                        password=os.getenv('PASSWORD'), port=os.getenv('PORT'))
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