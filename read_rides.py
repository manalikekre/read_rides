''' 
TBD
1. Modularize - different functions for auth, fetch_mail (gmail), parsing(beautifulSoup)
2. Docstrings for functions
3. Unit test cases
4. comments
5. Store & fetch data from mongoDB
'''
from __future__ import print_function
import httplib2
import os
import json
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
from io import StringIO
import base64
from bs4 import BeautifulSoup
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def oauth_setup():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    return http
    
def sync_mails(http):
    last_date = get_last_updated_date()
    mail_list = fetch_mails(http, last_date)
    mail_list_obj = parse_mails(mail_list)
    update_db(mail_list_obj)

def get_last_updated_date():
    return None

def fetch_mails( http, from_date = None):
    service = discovery.build('gmail', 'v1', http=http)
    user_id = 'me'
    if from_date is None:
        query = 'From:uber receipts before:2016/09/24'
    else:
        query = 'From:uber receipts before:2016/09/24 after:'+from_date
    response = service.users().messages().list(userId=user_id, q=query).execute()
    
    messages = []
    if 'messages' in response:
      mess = response['messages']
    message_list = []
    till = len(mess)
    for i in range(3):
        msg_id = mess[i]['id']
        message = service.users().messages().get(userId='me', id=msg_id).execute()
        message_list.append(message)
    return message_list    

def parse_mails(mail_list):
    list_trips = []
    for message in mail_list:
        file_data = base64.urlsafe_b64decode(message['payload']['parts'][0]['body']['data'].encode('UTF-8'))
        soup = BeautifulSoup(str(file_data), 'html.parser')
        #print (soup)
        date = soup.find_all('span', class_='date')
        date_soup = BeautifulSoup(str(date[0]), 'html.parser')
        #print ('on date : ',date_soup.span.get_text())
        date_val = date_soup.span.get_text()
        fare = soup.find_all('span', class_='header-fare')
        fare_soup = BeautifulSoup(str(fare[0]), 'html.parser')
        #print ('fare : ',fare_soup.span.get_text().strip())
        fare_val = fare_soup.span.get_text().strip().split()[1]
        from_time = soup.find_all('span', class_='from time')
        from_time_soup = BeautifulSoup(str(from_time[0]), 'html.parser')
        #print ('from time : ',from_time_soup.span.get_text())
        from_time_val = from_time_soup.span.get_text()
        to_time = soup.find_all('span', class_='to time')
        to_time_soup = BeautifulSoup(str(to_time[0]), 'html.parser')
        #print ('to time : ',to_time_soup.span.get_text())
        to_time_val = to_time_soup.span.get_text()
        address = soup.find_all('span', class_='address')
        from_address_soup = BeautifulSoup(str(address[0]), 'html.parser')
        to_address_soup = BeautifulSoup(str(address[1]), 'html.parser')
        #print ('from address : ',from_address_soup.span.get_text())
        #print ('to address : ',to_address_soup.span.get_text())
        from_add_val = from_address_soup.span.get_text()
        to_add_val = to_address_soup.span.get_text()
        #labels = soup.find_all('span', class_='label')
        datas = soup.find_all('span', class_='data')
        label_val = []
        for label, data in zip (labels, datas):
            #label_soup = BeautifulSoup(str(label), 'html.parser')
            data_soup = BeautifulSoup(str(data), 'html.parser')
            #print (label_soup.span.get_text(), ' : ', data_soup.span.get_text())
            label_val.append(data_soup.span.get_text())
  
        #charge_label = soup.find_all('span', class_='charge-label')
        #charge_label_soup = BeautifulSoup(str(charge_label[0]), 'html.parser')
        card_detail = soup.find_all('span', class_='card-detail')
        card_detail_soup = BeautifulSoup(str(card_detail[0]), 'html.parser')
        #print ( charge_label_soup.span.get_text(),' : ',card_detail_soup.span.get_text().strip())
        mop_val = card_detail_soup.span.get_text().strip()
        p = Trip (date_val, fare_val, from_time_val, to_time_val, from_add_val, to_add_val, label_val[0],label_val[1], label_val[2], mop_val)
        list_trips.append(p)
        print (p)
    return list_trips

def update_db(trip_obj_list):
    pass

class Trip:
    def __init__(self, date, fare, from_time, to_time, from_add, to_add, vehicle, distance, trip_time, mop):
        self.date = date
        self.fare = fare
        self.from_time = from_time
        self.to_time = to_time
        self.from_add = from_add
        self.to_add = to_add
        self.vehicle = vehicle
        self.distance = distance
        self.trip_time =trip_time
        self.mode_of_payment = mop

    def __str__(self):
        return "on date : "+self.date+" fare : "+self.fare+" from time : "+\
        self.from_time+" to time : "+self.to_time+"from address : "+\
        self.from_add+" to address : "+self.to_add+" vehicle : "+\
        self.vehicle+" distance : "+self.distance+" trip time : "+\
        self.trip_time+" mode of payment : "+self.mode_of_payment
def main():
    """Shows basic usage of the Gmail API.

    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """
    http = oauth_setup()
    sync_mails(http)
         
    

if __name__ == '__main__':
    main()