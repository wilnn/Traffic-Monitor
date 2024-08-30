###################

# This module is intended to run continuously 24/7. It will check the database and find new traffic incidents.
# Once new traffic incidents are found, it will email the user.

# This module is not the actual one that I deployed to the cloud to run because keeping a program running continuously is too
# expensive. I don't want to pay money for the cloud service ;) not until I can find a good free platform for this. 
# Check out my worker-aws-lambda.py module because it is the version that has been deployed. 

###################

from dotenv import load_dotenv
from bs4 import BeautifulSoup
from datetime import timedelta, timezone
import time, smtplib, os, datetime
import mysql.connector
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import services

'''
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

# get time until the next run for the closed (in time) entries in the table in seconds
def getSleepTime(ttime):
    notTimeZoneAware = datetime.datetime.now(tz=datetime.UTC)
    #turn not timezone aware object into naive 
    notTimeZoneAware2 = notTimeZoneAware.astimezone(timezone.utc).replace(tzinfo=None)
    #print("Time in db: "+str(ttime))
    #print("current time: "+str(notTimeZoneAware2))
    # find the time different between current time and the 
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

    # get traffic incident data
    data = services.trafficIncidentService(northeast, southwest)

    # if no inciddentID is in the selected row(first time run that row) then IncidentID is of nonetype not an empty string.
    # so need to replace with empty string to work in later code. 
    if not dataDB[9]:
        dataDB[9] = ''
    # if data is the traffic incident data and not an error message due to failure in sending request to 
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

# upadate the database with new value
def updateDB(cur, dataDB, id=[]):
    notTimeZoneAware = datetime.datetime.now(tz=datetime.UTC)
    #turn not timezone aware object into naive 
    notTimeZoneAware2 = notTimeZoneAware.astimezone(timezone.utc).replace(tzinfo=None)
    newNext_run = notTimeZoneAware2 + timedelta(minutes=dataDB[6])
    # if no new incidentID found (no new traffic problems)
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

# send email to user
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
    # body of the message
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
    # adding rows to the table
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
        print('error sending email: '+ str(e))
        return -1
    return 0

# delete incidentID if 24h have passed
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
    load_dotenv()
    conn = mysql.connector.connect(host=os.getenv('HOST'), database=os.getenv('DBNAME'), user=os.getenv('USER'), 
                        password=os.getenv('PASSWORD'), port=os.getenv('PORTT'))
    # continue sleeping if can not connect
    if not conn.is_connected():
        print("can not connect to the database")
        return 600
    #print(os.getenv('HOST'))
    #print(os.getenv('USER'))
    #print(os.getenv('DBNAME'), os.getenv('PORT'))
    cur = conn.cursor()

    # check database size and available storage
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
    cur.execute(query)

    results = cur.fetchall()
    # the current maximum storage is 10 MB. If the database size is >= 9.8 MB, will not add new entries
    if results[2][1] >= 9.8:
        return 600

    # this loop will keep running as long as there is a row that has its scheduled next_run time passed or is at the current time.
    while True:
        #handle the case when the table is empty
        cur.execute('''SELECT COUNT(*) FROM data''')
        if cur.fetchone()[0] == 0:
            seconds = 600
            break
        
        # sort the table ascending order of next_run value, then select the first row that has the smallest(closest) next_run time
        cur.execute('''SELECT * FROM data ORDER BY next_run ASC LIMIT 1''')
        dataDB = cur.fetchone()

        # convert dataDB from tuple type to list so that it can be modified
        dataDB = list(dataDB)
        #print(dataDB)
        seconds = getSleepTime(dataDB[8])
        
        # if time until the closest next_run is more than 5 second then sleep
        if seconds > 5:
            break
        id, from_, to_, detail = checkIncident(dataDB)

        # if no new traffic problems (incidentID) are found then will not send email to user.
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
    print('Sleeping for '+ str(seconds) + ' second(s)....')
    return seconds

if __name__ == "__main__":
    # this loop keep the module run continuously
    while True:
        seconds = main()
        # sleep until the next run time
        time.sleep(seconds)