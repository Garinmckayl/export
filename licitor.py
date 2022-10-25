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
               

                ls_links.append([link])
            print(link)
    # writeData.addRawData(ls_links)
    return ls_links