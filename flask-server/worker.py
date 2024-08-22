from dotenv import load_dotenv
from datetime import timedelta, timezone
import time, copy, smtplib, os, psycopg2, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import html
import services


'''CREATE TABLE IF NOT EXISTS data (
                 city varchar(200),
                 state varchar(100),
                 country varchar(100),
                 coordinate varchar(300)
                 email varchar(320),
                 interval int,
                 time TIMESTAMP PRIMARY KEY,
                 next_run timestamp without time zone,
                 id varchar(10000)'''

def getSleepTime(conn, cur, ttime):
    
    notTimeZoneAware = datetime.datetime.now(tz=datetime.UTC)
    #turn not timezone aware object into naive 
    notTimeZoneAware2 = notTimeZoneAware.astimezone(timezone.utc).replace(tzinfo=None)
    print("Time in db: "+str(ttime))
    print("current time: "+str(notTimeZoneAware2))
    # find the time different between current time and the 
    #smallest next run time in the db
    diff = ttime - notTimeZoneAware2
    print(diff.total_seconds())
    return diff.total_seconds()

# this function will checck for new incidents to report
def checkIncident(dataDB):
    id = []
    from_ = []
    to_ = []
    detail = []

    #northeast, southwest = services.geocodingService(dataDB[0], dataDB[1], dataDB[2])
    # convert the string to list
    coordinate = dataDB[3].split(',')

    northeast = {'lng': float(coordinate[0]), 'lat': float(coordinate[1])}
    southwest = {'lng': float(coordinate[2]), 'lat': float(coordinate[3])}

    data = services.trafficIncidentService(northeast, southwest)
    if not isinstance(data, str):
        for incident in data['incidents']:
            if incident['properties']['id'] in dataDB[8]:
                continue
            id.append(incident['properties']['id'][len(incident['properties']['id'])-3:])
            from_.append(incident['properties']['from'])
            to_.append(incident['properties']['to'])
            e = []
            for event in incident['properties']['events']:
                e.append(event['description'])
            detail.append(e)

    return id, from_, to_, detail

def updateDB(cur, dataDB, id=[]):
    #list is mutable so need to make a copy to avoid changing the original list
    if newTag:
        if newTag[0]:
            nv = [newTag[i][0] for i in range(0, len(newTag))]

    notTimeZoneAware = datetime.datetime.now(tz=datetime.UTC)
    #turn not timezone aware object into naive 
    notTimeZoneAware2 = notTimeZoneAware.astimezone(timezone.utc).replace(tzinfo=None)
    newNext_run = notTimeZoneAware2 + timedelta(minutes=dataDB[2])

    if not nv:
        query = '''UPDATE data SET next_run = %s WHERE data.time = %s'''
        value = (newNext_run, dataDB[3])
        cur.execute(query, value)
    else:
        for index, i in enumerate(dataDB[5]):
            if i not in nv:
                nv.insert(index, dataDB[6][index])
        print(type(nv))
        # turn python list into a string that look like an array in the format {..., ..., ...} to match with the array type in the database
        query = '''UPDATE data SET next_run = %s, tag = %s WHERE data.time = %s'''
        
        value = (newNext_run, nv, dataDB[3])
        cur.execute(query, value)

def sendEmail(oldTag, newTag, newValue, oldValue, changeType, email, url):
    message = MIMEMultipart()
    message["From"] = os.getenv('SENDER_EMAIL')
    message["To"] = email
    message["Subject"] = 'Change(s) Detected'
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
            <p>New change(s) detected at<a href={url}> the website</a> you provided</p>
            <p style='text-align: center; color: red; font-weight:bold; font-size:16px'>To stop receving email, please visit <a href="content-tracker.com">content-tracker.com</a> and enter your email at the bottom field.</p>
            <p style='text-align:center'>
                <table style="border-collapse: collapse;width: 100%;">
                    <thead>
                        <tr>
                            <th>Change Type</th>
                            <th>Old Value</th>
                            <th>New Value</th>
                            <th>Old tag</th>
                            <th>New tag</th>
                        </tr>
                    </thead>
                </table>
            </p>
            </body>
            </html>
        '''
    soup = BeautifulSoup(HTML, 'html.parser')
    table = soup.find('table')
    for i in range(0, len(oldTag)):
        new_row = soup.new_tag('tr')
        td1 = soup.new_tag('td')
        td1.string = changeType[i][0]
        td2 = soup.new_tag('td')
        td2.string = oldValue[i][0]
        td3 = soup.new_tag('td')
        td3.string = newValue[i][0]
        td4 = soup.new_tag('td', rowspan=str(len(oldTag[i])))
        #use html.escape to turn html format to html utility format so that it will not be render as html tag and be display as it is
        td4.string = html.escape(oldTag[i][0])
        td5 = soup.new_tag('td', rowspan=str(len(oldTag[i])))
        td5.string = html.escape(newTag[i][0])
        new_row.append(td1)
        new_row.append(td2)
        new_row.append(td3)
        new_row.append(td4)
        new_row.append(td5)
        table.append(new_row)
        print(new_row)
        for l in range(1, len(oldTag[i])):
            new_row = soup.new_tag('tr')
            td1 = soup.new_tag('td')
            td1.string = changeType[i][l]
            td2 = soup.new_tag('td')
            td2.string = oldValue[i][l]
            td3 = soup.new_tag('td')
            td3.string = newValue[i][l]
            new_row.append(td1)
            new_row.append(td2)
            new_row.append(td3)
            table.append(new_row)
            
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


def main():
    load_dotenv()
    conn = psycopg2.connect(host=os.getenv('HOST'), dbname=os.getenv('DBNAME'), user='postgres', 
                            password=os.getenv('PASSWORD'), port=os.getenv('PORT'))
    #print(os.getenv('HOST'))
    #print(os.getenv('USER'))
    #print(os.getenv('DBNAME'), os.getenv('PORT'))
    cur = conn.cursor()

    while True:
        #remove row with no value in id column
        cur.execute('''DELETE FROM data WHERE id IS NULL''')
        conn.commit()

        #handle the case when the table is empty
        cur.execute('''SELECT COUNT(*) FROM data''')
        conn.commit()
        if cur.fetchone()[0] == 0:
            seconds = 6000
            break

        cur.execute('''SELECT * FROM data ORDER BY next_run ASC LIMIT 1''')
        conn.commit()
        dataDB = cur.fetchone()
        #print(dataDB)

        seconds = getSleepTime(conn, cur, dataDB[7])
        
        if seconds > 5:
            break
        id, from_, to_, detail = checkIncident(dataDB)

        if id:
            updateDB(cur, dataDB, id)
            conn.commit()
            if sendEmail(from_, to_, detail) == -1:
                cur.execute(f'''DELETE FROM data WHERE time = {dataDB[6]}''')
                conn.commit()
        else:
            updateDB(conn, cur, dataDB)
            conn.commit()
    
    conn.close()
    cur.close()
    print('Sleeping for '+ str(seconds) + ' second(s)....')
    return seconds


if __name__ == "__main__":
    while True:
        seconds = main()
        time.sleep(seconds)