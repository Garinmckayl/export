# a module to send data to google the google sheet
import gspread
from oauth2client.service_account import ServiceAccountCredentials
scope=['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.readonly']
creds=ServiceAccountCredentials.from_json_keyfile_name('client_secret.json',scope)
client=gspread.authorize(creds)
sheet=client.open('Remereo').sheet1

