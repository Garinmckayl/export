import requests
from bs4 import BeautifulSoup
import writeData
from selenium.webdriver.common.by import By
import datetime
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from time import sleep
session=requests.Session()
def licitorScraping():
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    #get the current date
    date=datetime.datetime.now()
    #get the date it will be in 30 days
    date30=date+datetime.timedelta(days=30)
    #get the month and day
    month=date30.month
    day=date30.day
    year=date30.year
    url_page='https://www.licitor.com/dernieres-encheres.html?p={i}'
    ls_links=[]
    r=session.get(url_page.format(i=1))
    soup=BeautifulSoup(r.text,'html.parser')
    number_of_pages=int(soup.find('span',{'class':'PageTotal'}).text.split('/')[-1].strip())
    for i in range (1,number_of_pages+1):	
        print(i, 'Annonces : ', len(ls_links))
        r = session.get(url_page.format(i=i))
        soup = BeautifulSoup(r.text, "lxml")
        driver.get(url_page.format(i=i))
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
                'date':soup.find('time').get('datetime'),
                'city': li.find('span', {'class': 'City'}).text.strip().split('(')[0],
                'name':'',
                'surname':'',
                'phone':'',
                'zip':'',
                'address':'', 
                #find the street name from the element of class Street
                'street':'',
                
            }
            originalType=li.find('span', {'class': 'Name'}).text.strip()
            dateArray=link['date'].split('T')[0].split('-')
            if int(dateArray[1])==month and int(dateArray[2])==day and int(dateArray[0])==year\
            and'maison' in originalType or 'pavillon' in originalType and link['date']: 
                sleep(2) 
                link = {
                    'link': 'https://www.licitor.com' + li.find('a').get('href'),
                    'date':soup.find('time').get('datetime'),
                    'city': li.find('span', {'class': 'City'}).text.strip().split('(')[0],
                    'name':'',
                    'surname':'',
                    'phone':'',
                    'zip':'',
                    'address':'', 
                    #find the Street Tag. Then put a space instead of the br tag 
                    'street':driver.find_element(By.CLASS_NAME,'Street').get_attribute('innerHTML').replace('<br>',' '),
                    
                    
                }
                
                #Converts the date tag to a format
                print(date)
                #filter for only the dates that are in exactly one month
                

                
                ls_links.append([link])
                print(link)
    # writeData.addRawData(ls_links)
    return ls_links