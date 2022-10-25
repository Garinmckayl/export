import requests
from bs4 import BeautifulSoup
import writeData
session=requests.Session()
def licitorScraping():
    url_page='https://www.licitor.com/dernieres-encheres.html?p={i}'
    ls_links=[]
    r=session.get(url_page.format(i=1))
    soup=BeautifulSoup(r.text,'html.parser')
    number_of_pages=int(soup.find('span',{'class':'PageTotal'}).text.split('/')[-1].strip())
    for i in range (1,number_of_pages+1):	
        print(i, 'Annonces : ', len(ls_links))
        r = session.get(url_page.format(i=i))
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
            writeData.addRawData(link)