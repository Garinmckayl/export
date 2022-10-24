# -*- coding: utf-8 -*-

import os
from docx import Document
from datetime import datetime
import locale
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
import requests
import base64
from google.oauth2.service_account import Credentials
import gspread

locale.setlocale(locale.LC_TIME, "French_France.1252")
dir_path = os.path.dirname(os.path.realpath(__file__))
   
CREDENTIALS_DRIVE = os.path.join(dir_path, 'credentials', 
                                 'credentials.json')

# Drive Folder ID to store temporary files and mail files
DRIVE_FOLDER_ID = ''  
SERVICEPOSTAL_API_KEY = "f6556dfe948f58c57650fc8c13294030"
template_file = os.path.join(dir_path, 'templates', 
                             'template_mail_licitor.docx')

folder = os.path.join( dir_path, 'mails')
url_export_drive = "https://docs.google.com/document/u/0/export?format=pdf&id={drive_file_id}&access_token={access_token}"

def getGAuth():
    gauth = GoogleAuth()
    scope = ["https://www.googleapis.com/auth/drive"]
    gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_DRIVE, scope)
    
    return gauth

def send_file_to_drive(file_path):   
    gauth = getGAuth()
    drive = GoogleDrive(gauth)
    
    file = drive.CreateFile({"parents": [{"id": DRIVE_FOLDER_ID}]})
    file['title'] = os.path.basename(file_path)
    file.SetContentFile(file_path)
    file.Upload()
    
    return file['id']

def get_drive_doc_to_base64_pdf(drive_file_id):
    gauth = getGAuth()
    access_token = gauth.credentials.get_access_token()[0]
    
    r = requests.get(url_export_drive.format(drive_file_id=drive_file_id, 
                                             access_token=access_token)) 
    
    return base64.b64encode(r.content)

def get_processed_announces(spreadsheet_id, worksheet_key):
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    credentials = Credentials.from_service_account_file(
        CREDENTIALS_DRIVE,
        scopes=scopes
    )
    gc = gspread.authorize(credentials)
    wb = gc.open_by_key(spreadsheet_id)
    ws = wb.get_worksheet_by_id(worksheet_key)
    
    return ws.get_all_records(numericise_ignore=['all'])

def sheet_insert_row(spreadsheet_id, worksheet_key, data):
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    credentials = Credentials.from_service_account_file(
        CREDENTIALS_DRIVE,
        scopes=scopes
    )
    gc = gspread.authorize(credentials)
    wb = gc.open_by_key(spreadsheet_id)
    ws = wb.get_worksheet_by_id(worksheet_key)
    
    return ws.append_row(data)  


if not os.path.exists(folder):
    os.makedirs(folder)
    

def send_mail(data, source):
    
    print("Modification du template")
    doc = Document(template_file)
    
    for paragraph in doc.paragraphs:
        for data_key in data:
            if '{' + data_key + '}' in paragraph.text:
                paragraph.text = paragraph.text.replace('{' + data_key + '}',
                                                        data[data_key].upper())
    
    dt_file = datetime.now().strftime('%Y%m%d')
    export_file_doc = os.path.join(folder, f'{dt_file}_{data["reference_id"]}_{source}_courrier.docx')
    doc.save(export_file_doc)
    
    print("Import sur Google Drive et export PDF")
    drive_file_id = send_file_to_drive(export_file_doc)
    file_base64_pdf = get_drive_doc_to_base64_pdf(drive_file_id)
    
    
    print("Envoi des données")    
    body = {
          "type_enveloppe": "c6",
          "adresse_expedition":
              {
                  "prenom": "",
                  "nom": "",
                  "nom_societe": "REMEREO",
                  "adresse_ligne1": "11 Rue de Magdebourg",
                  "adresse_ligne2": "",
                  "code_postal": "75116",
                  "ville": "Paris",
                  "pays": "France"
                  },
          "adresse_destination":
              {
                  "prenom": "", #data["prenom"],
                  "nom": "",
                  "nom_societe": data["nom_prenom"],
                  "adresse_ligne1": data["adresse"],
                  "adresse_ligne2": "",
                  "code_postal": data["code_postal"],
                  "ville": data["ville"],
                  "pays": data["pays"]
                  },         
          "fichier": {
              "format": "pdf",
              "contenu_base64": file_base64_pdf.decode('ascii')
              },
          "type_affranchissement": "prioritaire",
          "couleur": "nb",
          "recto_verso": "recto",
          "placement_adresse": "premiere_page",
          "impression_expediteur": False
          }
    
    url_service_postal = "https://prod-api.servicepostal.com/lettres"
    
    headers = {
        'apiKey': SERVICEPOSTAL_API_KEY
        }
    
    r = requests.post(url_service_postal, json=body, headers=headers)
    
    return r
    