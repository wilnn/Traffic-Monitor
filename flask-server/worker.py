from scrape import Scrape
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import timedelta, timezone
import time, copy, smtplib, os, psycopg2, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import html

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

def checkContent(dataDB):
    newValue = []
    oldValue = []
    changeType = []
    newTag = []
    oldTag = []
    #if can not scrape
    data = Scrape(dataDB[0])
    content = data.scrape()
    soup = data.getModifiedHTML(content)
    soup = BeautifulSoup(soup.prettify(), 'html.parser')
    #find change in text
    for index, idd in enumerate(dataDB[5]):
        print("&777777", index)
        print(dataDB[6][index])
        minisoup = BeautifulSoup(dataDB[6][index], 'html.parser')
        print(minisoup)
        minisoup.find(id=idd).unwrap()
        tag = soup.find(id=idd)
        print("soup: ", soup)
        print("id:", idd)
        print("type", type(soup))
        print("type", type(minisoup))
        print("tag: ", tag)
        print(tag)
        parent = tag.parent
        parent.span.unwrap()
        print("lennnnnn", len(newValue))
        if (len(newValue) < (index+1)):
                oldTag.append([])
                print("llllllllllll", oldTag)
                newTag.append([])
                oldValue.append([])
                newValue.append([])
                changeType.append([])
        parenttext = ' '+ parent.get_text().strip() +' '
        minisouptext = ' ' + minisoup.get_text().strip() + ' '
        if  parenttext != minisouptext:
            print("8888888888888", index)
            print("9999999999999", len(oldTag))
            oldTag[index].append(str(minisoup.prettify()))
            newTag[index].append(str(parent.prettify()))
            oldValue[index].append(minisouptext)
            newValue[index].append(parenttext)
            changeType[index].append('Change in content')

        if parent.name != minisoup.contents[0].name:
            oldTag[index].append(str(minisoup.prettify()))
            newTag[index].append(str(parent.prettify()))
            oldValue[index].append(str(minisoup.contents[0].name))
            newValue[index].append(str(parent.name))
            changeType[index].append('Change in tag name')
        
        if len(parent.attrs) > len(minisoup.contents[0].attrs):

            big = parent.attrs
            small = minisoup.contents[0].attrs
        else:
            big = minisoup.contents[0].attrs
            small = parent.attrs
        for key in (list(big.keys())):
            if key not in list(small.keys()):
                oldTag[index].append(str(minisoup.prettify()))
                newTag[index].append(str(parent.prettify()))
                oldValue[index].append('not having that attribute before or it was removed')
                newValue[index].append(key+ ' = '+ big[key])
                changeType[index].append('new attribute added/removed')
            elif minisoup.contents[0].attrs[key] != parent.attrs[key]:
                oldTag[index].append(str(minisoup.prettify()))
                newTag[index].append(str(parent.prettify()))
                oldValue[index].append(minisoup.contents[0].attrs)
                newValue[index].append(parent.attrs[key])
                changeType[index].append("Change in attribute's value")
        if not newTag[-1]:
            oldTag.pop()
            newTag.pop()
            oldValue.pop()
            newValue.pop()
            changeType.pop()
    print(changeType)
    return newTag, oldTag, newValue, oldValue, changeType

def updateDB(cur, dataDB, newTag=[]):
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
        return 0
    return 1


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

        seconds = getSleepTime(conn, cur, dataDB[6])
        
        if (seconds > 5):
            break
        newTag, oldTag, newValue, oldValue, changeType = checkContent(dataDB)

        #print(newTag)
        if newTag:
            updateDB(cur, dataDB, newTag)
            conn.commit()
            if not sendEmail(oldTag, newTag, newValue, oldValue, changeType, dataDB[1], dataDB[0]):
                cur.execute(f'''DELETE FROM data WHERE time = {dataDB[3]}''')
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