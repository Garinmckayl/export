import requests
from bs4 import BeautifulSoup
import writeData
import datetime
session=requests.Session()
def licitorScraping():
    #get the current date
    date=datetime.datetime.now()
    #get the month and day
    month=date.month
    day=date.day
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
                'date':soup.find('time'),
                

                'department': li.find('span', {'class': 'Number'}).text.strip(),
                'city': li.find('span', {'class': 'City'}).text.strip().split('(')[0],
            }
            originalType=li.find('span', {'class': 'Name'}).text.strip()
            #Converts the date tag to a mm/dd/yyyy format
            date=link['date'].split('\"')[1].split('-')[0:3]
            print(date)
            if 'maison' in originalType or 'pavillon' in originalType and link['date']: 
               

                ls_links.append([link])
            print(link)
    # writeData.addRawData(ls_links)
    return ls_links