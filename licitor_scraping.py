# -*- coding: utf-8 -*-
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from urllib import parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

# import envoi_mail_licitor_remereo as envoi_email

dt_today = datetime.today()
dir_path = os.path.dirname(os.path.realpath(__file__))
folder = os.path.join(dir_path, 'files')

if not os.path.exists(folder):
    os.makedirs(folder)

CREDENTIALS_DRIVE = os.path.join(dir_path, 'credentials',
                                 'credentials.json')
# Google Drive ID File with Licitor Data
DRIVE_FILE_CONTACTS_ID = ''
# Google Drive ID File with Mail Sent
LISTING_MAILS_SENT_DRIVE_ID = ''
LISTING_MAILS_SENT_DRIVE_WORKSHEET_KEY = 0
LISTING_MAILS_SENT_DRIVE_ERROR_WORKSHEET_KEY = 1


def getGAuth():
    gauth = GoogleAuth()
    scope = ["https://www.googleapis.com/auth/drive"]
    gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_DRIVE, scope)

    return gauth


def send_file_to_drive(file_path):
    gauth = getGAuth()
    drive = GoogleDrive(gauth)

    file = drive.CreateFile({'id': DRIVE_FILE_CONTACTS_ID})
    file.SetContentFile(file_path)
    file.Upload()


s = requests.Session()
url_api_entreprise = 'https://recherche-entreprises.api.gouv.fr/search'
url_pages_blanches = 'https://www.pagesjaunes.fr/pagesblanches/recherche?ou='

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()

# Get list of announces
ls_links = []
url_page = "https://www.licitor.com/dernieres-encheres.html?p={i}"

r = s.get(url_page.format(i=1))
soup = BeautifulSoup(r.text, "lxml")

total_pages = int(soup.find('span', {'class': 'PageTotal'})
                      .text.split('/')[-1].strip())


for i in range(1, total_pages+1):
    print(i, 'Annonces : ', len(ls_links))
    r = s.get(url_page.format(i=i))
    soup = BeautifulSoup(r.text, "lxml")

    page_number = int(
        soup.find('input', {'type': 'text', 'name': 'p'}).get('value'))
    if page_number != i:
        break

    ul_ad = soup.find("ul", {"class": "AdResults"})
    for li in ul_ad.find_all('li'):
        if not li.find('a'):
            continue

        link = {
            'link': 'https://www.licitor.com' + li.find('a').get('href'),
            'department': li.find('span', {'class': 'Number'}).text.strip(),
            'city': li.find('span', {'class': 'City'}).text.strip().split('(')[0],
            'originalType': li.find('span', {'class': 'Name'}).text.strip()
        }

        if 'maison' in link['originalType'] or 'pavillon' in link['originalType'] \
                or 'propriété' in link['originalType'] or 'remise' in link['originalType']:
            link['type'] = 'Maison'
        elif 'appartement' in link['originalType'] or 'logement' in link['originalType'] \
                or 'Un bien' in link['originalType'] or 'Une pièce' in link['originalType'] \
                or 'studio' in link['originalType']:
            link['type'] = 'Appartement'
        elif 'immeuble' in link['originalType'] or 'bâtiment' in link['originalType'] \
                or 'bâtisse' in link['originalType'] or 'ensemble' in link['originalType']:
            link['type'] = 'Immeuble'
        else:
            link['type'] = 'Autres'

        ls_links.append(link)

    # i+=1

# remove duplicates
ls_links = [dict(t) for t in {tuple(d.items()) for d in ls_links}]

# Get announces content
for result in ls_links:
    # if result['link'] != 'https://www.licitor.com/annonce/09/22/73/vente-aux-encheres/une-maison-d-habitation/mantes-la-ville/yvelines/092273.html':
    #     continue

    if 'location' in result or 'toBeProcessed' in result:
        continue

    print(ls_links.index(result))
    k = 0
    while k < 2:
        try:

            if k > 0:
                print('retry', k)

            r = s.get(result['link'])
            break
        except:
            k += 1
            r = None

    if not r:
        print("error fetching data")
        continue

    soup = BeautifulSoup(r.text, "lxml")

    if 'https://www.licitor.com/404.html?' in r.url:
        result['toBeProcessed'] = False
        print('error 404')
        continue

    result['id'] = soup.find('p', {'class': 'Number'}).text.strip()
    result['auctionDate'] = soup.find('p', {'class': 'Date'}).find(
        'time').get('datetime').strip()

    if not (datetime.strptime(result['auctionDate'], '%Y-%m-%dT%H:%M:%S') - dt_today).days >= 30:
        result['toBeProcessed'] = False
        print('Announce too old')
        continue
    else:
        result['toBeProcessed'] = True

    try:
        result['description'] = ' '.join([x.strip() for x in list(
            soup.find('div', {'class': 'FirstSousLot SousLot'}).stripped_strings)])
    except:
        result['description'] = None

    try:
        result['location'] = ' '.join([x.strip() for x in list(
            soup.find('p', {'class': 'Street'}).stripped_strings)])
        if result['location'].startswith('Route départementale '):
            result['location'] = result['location'].replace(
                'Route départementale ', 'D')
        result['location'] = result['location'].replace(',', ' ')
    except:
        result['location'] = None

    try:
        result['startingPrice'] = [x.text.split(':')[-1].strip() for x in
                                   soup.find_all('h3') if x.text.startswith('Mise à prix')][0]
    except:
        result['startingPrice'] = None

    # find postal/city code
    maps_link = soup.find('p', {'class': 'Map'})
    if not maps_link or not result['location']:
        continue

    maps_coordinates = parse.parse_qs(
        parse.urlsplit(maps_link.find('a').get('href')).query)
    result['latitude'] = maps_coordinates['q'][0].split(',')[0]
    result['longitude'] = maps_coordinates['q'][0].split(',')[1]

    api_address = '{0} {1}'.format(result['location'], result['city'])
    api_lat = result['latitude']
    api_lon = result['longitude']

    url_adresse = f'https://api-adresse.data.gouv.fr/search/?q={api_address}&lat={api_lat}&lon={api_lon}'
    r_api = s.get(url_adresse)
    # result['api_adresse_licitor'] = url_adresse
    api_data = r_api.json()['features']
    if not api_data:
        print('Api Address KO', result)
        print(r_api.status_code)
        print(r_api.url)
        continue

    api_min_distance = min([x['properties']['distance'] for x in api_data])
    api_data = [x for x in api_data if x['properties']
                ['distance'] == api_min_distance][0]

    if api_data['properties']['postcode'][:2] == result['department']:

        result['postalCode'] = api_data['properties']['postcode']
        result['cityCode'] = api_data['properties']['citycode']
        result['region'] = api_data['properties']['context']
        result['street'] = api_data['properties']['name']

        # check if company
        r_entreprise = s.get(url_api_entreprise, params={'q': result['street'],
                                                         'code_postal': result['postalCode'],
                                                         'department': result['department'],
                                                         'per_page': 50})

        if r_entreprise.status_code == 200:
            data_entreprise = r_entreprise.json()
            # data_entreprise['total_results']
            result['api_entreprise_total_results'] = 0

            ls_entreprises = []
            for entreprise in data_entreprise['results']:
                if entreprise['etat_administratif'] != 'A':
                    continue

                r_api = s.get(
                    f"https://api-adresse.data.gouv.fr/search/?q={entreprise['siege']['adresse_complete']}")
                # print(r_api.url)
                api_data_entreprise = r_api.json()['features']
                if not api_data_entreprise:
                    continue

                for _row in api_data_entreprise:
                    if _row['properties']['score'] >= 0.7 \
                            and _row['properties']['name'] == result['street'] \
                            and _row['properties']['postcode'] == result['postalCode']:
                        ls_entreprises.append(' - '.join([
                            entreprise['nom_complet'].replace('-', ' '),
                            entreprise['siege']['siret'],
                            entreprise['etat_administratif'],
                            entreprise['siege']['adresse_complete']
                        ]))
                        result['api_entreprise_total_results'] += 1
                        break

            result['api_entreprises_results'] = '\n'.join(ls_entreprises)

    # check in phone book
    if 'street' in result:
        pages_blanches_address = ' '.join([result['street'],
                                           result['postalCode'],
                                           result['city']])
    else:
        pages_blanches_address = ' '.join([result['location'],
                                           result['city'],
                                           result['department']])
    driver.get(f"{url_pages_blanches}{pages_blanches_address}")

    hasDriverReponse = False

    try:
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID,
                                                                         'SEL-nbresultat')))
        hasDriverReponse = True

    except:
        continue

    try:
        if not hasDriverReponse:
            WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID,
                                                                             'wording-no-responses')))
            print('No responses')
            continue
    except:
        pass

    try:
        if hasDriverReponse:
            no_pages_blanches_responses = driver.find_element_by_tag_name('body').get_attribute('innerHTML').find(
                "Nous n'avons pas trouvé de résultats pour votre recherche sur PagesBlanches. Vous avez été redirigé vers PagesJaunes, le service de recherche de professionnels")
            if no_pages_blanches_responses >= 0:
                print('No pages blanches data')
                continue
    except:
        pass

    time.sleep(3)

    cookies_validation_button = driver.find_elements(By.ID,
                                                     'didomi-notice-agree-button')
    if cookies_validation_button:
        cookies_validation_button[0].click()
        time.sleep(4)

    ls_pages_blanches_part_results = []
    ls_pages_blanches_entreprise_results = []
    ls_pages_blanches_results_li = driver.find_elements(By.CLASS_NAME,
                                                        'bi.bi-generic')

    for pb_result in ls_pages_blanches_results_li:

        pb_name = pb_result.find_element(By.CLASS_NAME,
                                         'bi-denomination.pj-link').text.strip()
        # if 'Ferme dans' in pb_name:
        #     stop
        try:
            pb_address = pb_result.find_element(By.CLASS_NAME,
                                                'bi-address.small').text.split(' Voir le plan')[0]
        except:
            pb_address = ''

        ls_pb_phone = []
        try:
            ls_pb_phones_div = pb_result.find_elements(By.CLASS_NAME,
                                                       'number-contact.txt_sm')
            for pb_phone_div in ls_pb_phones_div:
                pb_phone_html = pb_phone_div.get_attribute('innerHTML')

                if pb_phone_html.split('<')[0].find('Tél :') >= 0:
                    pb_phone_str = pb_phone_div.find_elements(By.TAG_NAME,
                                                              'span')[-1].get_attribute('innerHTML').strip()
                    ls_pb_phone.append(pb_phone_str)
        except:
            pass

        pages_blanches_result = ' - '.join([pb_name.replace('-', ' '),
                                            pb_address,
                                            ] + ls_pb_phone)
        if pb_result.get_attribute('id').startswith('epj'):
            ls_pages_blanches_entreprise_results.append(pages_blanches_result)
        else:
            ls_pages_blanches_part_results.append(pages_blanches_result)

    result['pages_blanches_entreprise_results'] = '\n'.join(
        ls_pages_blanches_entreprise_results)
    result['pages_blanches_total_entreprise_results'] = len(
        ls_pages_blanches_entreprise_results)
    result['pages_blanches_particuliers_results'] = '\n'.join(
        ls_pages_blanches_part_results)
    result['pages_blanches_total_particulier_results'] = len(
        ls_pages_blanches_part_results)


driver.quit()

dt_now = datetime.now().strftime('%Y%m%d_%H%M%S')
export_file = os.path.join(folder, f"{dt_now}_export_data_licitor.xlsx")
df = pd.DataFrame(ls_links)
df = df[df['toBeProcessed'] == True]
df.sort_values(by=['auctionDate', 'department'],
               ascending=[True, True], inplace=True)
del df['toBeProcessed']

with pd.ExcelWriter(export_file) as writer:
    for _type in sorted(df['type'].drop_duplicates().tolist()) + ['Lead']:
        if _type == 'Lead':
            df_lead = df[(df['pages_blanches_total_entreprise_results'] == 1)
                         | (df['pages_blanches_total_particulier_results'] == 1)
                         | (df['api_entreprise_total_results'] == 1)]
            df_lead.to_excel(writer, sheet_name=_type, index=False)
        else:
            df[df['type'] == _type].to_excel(
                writer, sheet_name=_type, index=False)

        workbook = writer.book
        worksheet = writer.sheets[_type]
        cell_format = workbook.add_format()
        cell_format.text_wrap = True
        cell_format.set_align('vcenter')

        cell_align = workbook.add_format()
        cell_align.set_align('vcenter')

        worksheet.set_column('A:AZ', cell_format=cell_align)
        worksheet.set_column('R:R', cell_format=cell_format)
        worksheet.set_column('S:S', cell_format=cell_format)
        worksheet.set_column('U:U', cell_format=cell_format)

        for idx, col in enumerate(df):  # loop through all columns
            series = df[col]
            if col in ['pages_blanches_entreprise_results',
                       'pages_blanches_particuliers_results',
                       'api_entreprises_results']:
                worksheet.set_column(idx, idx, 60)  # set column width
            elif not col in ['description', 'link', 'location']:
                max_len = max((
                    series.astype(str).map(len).max(),  # len of largest item
                    len(str(series.name))  # len of column name/header
                )) + 1  # adding a little extra space
                worksheet.set_column(idx, idx, max_len)  # set column width
            else:
                worksheet.set_column(idx, idx, 10)

send_file_to_drive(export_file)

# send mails
ls_processed_records = envoi_email.get_processed_announces(LISTING_MAILS_SENT_DRIVE_ID,
                                                           LISTING_MAILS_SENT_DRIVE_WORKSHEET_KEY)

dict_lead_results = {
    'API Société': 'api_entreprises_results',
    'Pages Blanches Entreprise': 'pages_blanches_entreprise_results',
    'Pages Blanches Particulier': 'pages_blanches_particuliers_results'
}

dict_lead_total = {
    'API Société': 'api_entreprise_total_results',
    'Pages Blanches Entreprise': 'pages_blanches_total_entreprise_results',
    'Pages Blanches Particulier': 'pages_blanches_total_particulier_results'
}

for lead in df_lead.to_dict('records'):

    for lead_type in ['API Société', 'Pages Blanches Entreprise',
                      'Pages Blanches Particulier']:

        if len([x for x in ls_processed_records
                if x['ID'] == lead['id'] and x['source'] == lead_type]) > 0:
            continue

        if lead[dict_lead_total[lead_type]] != 1:
            continue

        lead_info = lead[dict_lead_results[lead_type]]

        if not lead_info:
            continue

        print(lead_type, lead)
        mail_data = {
            "dt_today": datetime.now().strftime('%d %B %Y'),
            "nom_prenom": lead_info.split('-')[0].strip().upper(),
            "adresse": lead['street'],
            "code_postal": lead['postalCode'],
            "ville": lead['city'],
            "pays": "France",
            "reference_id": lead['id'],
        }

        if len([x for x in ls_processed_records
                if x['ID'] == lead['id']
                and mail_data['nom_prenom'] == x['destinataire']]) > 0:
            print('already_processed')
            continue

        r_mail = envoi_email.send_mail(mail_data, lead_type)

        listing_data = [
            mail_data['dt_today'],
            lead['id'],
            lead['link'],
            lead['auctionDate'],
            lead['description'],
            lead['location'],
            lead['startingPrice'],
            lead['department'],
            lead['city'],
            lead['postalCode'],
            lead['cityCode'],
            lead['region'],
            lead['street'],
            mail_data['nom_prenom'],
            lead_type
        ]

        if r_mail.status_code != 200:
            envoi_email.sheet_insert_row(LISTING_MAILS_SENT_DRIVE_ID,
                                         LISTING_MAILS_SENT_DRIVE_ERROR_WORKSHEET_KEY,
                                         listing_data + [r_mail.text])
            continue

        if r_mail.status_code == 200 and 'code' in r_mail.json():
            envoi_email.sheet_insert_row(LISTING_MAILS_SENT_DRIVE_ID,
                                         LISTING_MAILS_SENT_DRIVE_ERROR_WORKSHEET_KEY,
                                         listing_data + [r_mail.text])
            continue

        listing_data = [
            mail_data['dt_today'],
            lead['id'],
            lead['link'],
            lead['auctionDate'],
            lead['description'],
            lead['location'],
            lead['startingPrice'],
            lead['department'],
            lead['city'],
            lead['postalCode'],
            lead['cityCode'],
            lead['region'],
            lead['street'],
            mail_data['nom_prenom'],
            lead_type
        ]

        envoi_email.sheet_insert_row(LISTING_MAILS_SENT_DRIVE_ID,
                                     LISTING_MAILS_SENT_DRIVE_WORKSHEET_KEY,
                                     listing_data)
