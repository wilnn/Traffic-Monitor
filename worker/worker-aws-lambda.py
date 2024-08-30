import json
# no need for load_dotenv because I have added the environment 
#from dotenv import load_dotenv
from bs4 import BeautifulSoup
from datetime import timedelta, timezone
import time, smtplib, os, datetime
import mysql.connector
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import services

'''CREATE TABLE IF NOT EXISTS data (
                 ID varchar(7) PRIMARY KEY,
                 city varchar(200),
                 state varchar(100),
                 country varchar(100),
                 coordinate varchar(300)
                 email varchar(320),
                 timeInterval int,
                 time DATETIME,
                 next_run DATETIME,
                 incidentID varchar(10000)'''

def getSleepTime(ttime):
    notTimeZoneAware = datetime.datetime.now(tz=datetime.UTC)
    #turn not timezone aware object into naive 
    notTimeZoneAware2 = notTimeZoneAware.astimezone(timezone.utc).replace(tzinfo=None)
    #print("Time in db: "+str(ttime))
    #print("current time: "+str(notTimeZoneAware2))
    #find the time different between current time and the 
    #smallest next run time in the db
    diff = ttime - notTimeZoneAware2
    #print(diff.total_seconds())
    return diff.total_seconds()

# this function will checck for new incidents to report
def checkIncident(dataDB):
    id = []
    from_ = []
    to_ = []
    detail = []

    #northeast, southwest = services.geocodingService(dataDB[1], dataDB[2], dataDB[3])
    # convert the string to list
    coordinate = dataDB[4].split(',')

    northeast = {'lng': float(coordinate[0]), 'lat': float(coordinate[1])}
    southwest = {'lng': float(coordinate[2]), 'lat': float(coordinate[3])}

    data = services.trafficIncidentService(northeast, southwest)
    if not dataDB[9]:
        dataDB[9] = ''
    if not isinstance(data, str):
        for incident in data['incidents']:
            if incident['properties']['id'][len(incident['properties']['id'])-3:] in dataDB[9]:
                continue
            # need to trim down the given incident id to 4 letters long to save storage space
            id.append(incident['properties']['id'][len(incident['properties']['id'])-3:])
            from_.append(incident['properties']['from'])
            to_.append(incident['properties']['to'])
            e = []
            for event in incident['properties']['events']:
                e.append(event['description'])
            detail.append(e)

    return id, from_, to_, detail

def updateDB(cur, dataDB, id=[]):
    notTimeZoneAware = datetime.datetime.now(tz=datetime.UTC)
    #turn not timezone aware object into naive 
    notTimeZoneAware2 = notTimeZoneAware.astimezone(timezone.utc).replace(tzinfo=None)
    newNext_run = notTimeZoneAware2 + timedelta(minutes=dataDB[6])

    if not id:
        query = '''UPDATE data SET next_run = %s WHERE ID = %s'''
        value = (newNext_run, dataDB[0])
        cur.execute(query, value)
    else:
        id = ','.join(id)
        id = dataDB[9] + id
        # turn python list into a string that look like an array in the format {..., ..., ...} to match with the array type in the database
        query = '''UPDATE data SET next_run = %s, incidentID = %s WHERE ID = %s'''
        
        value = (newNext_run, id, dataDB[0])
        cur.execute(query, value)

def sendEmail(from_, to_, detail, email, city, state, country):
    message = MIMEMultipart()
    message["From"] = os.getenv('SENDER_EMAIL')
    message["To"] = email
    message["Subject"] = 'Traffic Incident(s) Detected'
    if not state:
        loc = f'{city}, {country}'
    else:
        loc = f'{city}, {state}, {country}'
    url = 'https://traffic-monitor.pages.dev/#unregister'
    HTML = f'''
            <html>
            <head>
            <style>
                th, td {{border: 1px solid black;
                padding: 8px;
                text-align: left;}}
            </style>
            </head>
            <body>
            <p>Traffic incident(s) detected in <strong>{loc}</strong></p>
            <p style='text-align: center; color: red; font-weight:bold; font-size:16px'>To stop receving email, please visit <a href="{url}" style="color:blue;">Traffic Monitor</a> and enter your email at the bottom field.</p>
            <p style='text-align:center'>
                <table style="border-collapse: collapse;width: 100%;">
                    <thead>
                        <tr>
                            <th>From</th>
                            <th>To</th>
                            <th>Detail</th>
                        </tr>
                    </thead>
                </table>
            </p>
            </body>
            </html>
        '''
    soup = BeautifulSoup(HTML, 'html.parser')
    table = soup.find('table')
    for i in range(0, len(from_)):
        new_row = soup.new_tag('tr')
        td1 = soup.new_tag('td')
        td1.string = from_[i]
        td2 = soup.new_tag('td')
        td2.string = to_[i]
        td3 = soup.new_tag('td')
        td3.string = ", ".join(detail[i])
        new_row.append(td1)
        new_row.append(td2)
        new_row.append(td3)
        table.append(new_row)
        #print(new_row)

    # Attach the HTML content
    message.attach(MIMEText(str(soup.prettify()), "html"))

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
        #print('error sending email: '+ str(e))
        return -1
    return 0

def resetID(cur, nextRun, originalTime, id):
    notTimeZoneAware = datetime.datetime.now(tz=datetime.UTC)
    #turn not timezone aware object into naive 
    notTimeZoneAware2 = notTimeZoneAware.astimezone(timezone.utc).replace(tzinfo=None)
    diff = nextRun - originalTime
    second = diff.total_seconds()
    # if 24 hours or more have passed
    if (second / 86400) >= 1:
        query = '''UPDATE data SET time = %s, incidentID = %s WHERE ID = %s'''
        value = (notTimeZoneAware2, '', id)
        cur.execute(query, value)

def main():
    conn = mysql.connector.connect(host=os.getenv('HOST'), database=os.getenv('DBNAME'), user=os.getenv('USER'), 
                        password=os.getenv('PASSWORD'), port=os.getenv('PORTT'))
    if not conn.is_connected():
        #print("can not connect to the database")
        return
    #print(os.getenv('HOST'))
    #print(os.getenv('USER'))
    #print(os.getenv('DBNAME'), os.getenv('PORT'))
    cur = conn.cursor()

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
        return

    while True:
        #handle the case when the table is empty
        cur.execute('''SELECT COUNT(*) FROM data''')
        if cur.fetchone()[0] == 0:
            #seconds = 600
            break

        cur.execute('''SELECT * FROM data ORDER BY next_run ASC LIMIT 1''')
        dataDB = cur.fetchone()
        # convert dataDB from tuple type to list so that it can be modified
        dataDB = list(dataDB)
        #print(dataDB)
        seconds = getSleepTime(dataDB[8])
        
        if seconds > 5:
            break
        id, from_, to_, detail = checkIncident(dataDB)

        if id:
            updateDB(cur, dataDB, id)
            conn.commit()
            if sendEmail(from_, to_, detail, dataDB[5], dataDB[1], dataDB[2], dataDB[3]) == -1:
                cur.execute(f'''DELETE FROM data WHERE ID = {dataDB[0]}''')
                conn.commit()
        else:
            updateDB(cur, dataDB)
            conn.commit()
        resetID(cur, dataDB[8], dataDB[7], dataDB[0])
    
    conn.close()
    cur.close()
    #print('Sleeping for '+ str(seconds) + ' second(s)....')
    return

def lambda_handler(event, context):
    main()
    return {
        'statusCode': 200,
        'body': json.dumps('Finished running.')
    }
