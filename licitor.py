import requests
from bs4 import BeautifulSoup
import writeData
from selenium.webdriver.common.by import By
import datetime
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from time import sleep
from pagesBlanches import pagesBlanches
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
            sleep(1)
            link = {
                'url': 'https://www.licitor.com' + li.find('a').get('href'),
               #get the date from the second time tag
                'date': driver.find_elements(By.TAG_NAME,'time')[2].get_attribute('datetime').split('T')[0],
                'city': li.find('span', {'class': 'City'}).text.strip().split('(')[0],
                'name':'',
                'surname':'',
                'phone':'',
                'zip':'',
                'address':'', 
                #find the street name from the element of class Street
                'street':driver.find_element(By.CLASS_NAME,'Street').get_attribute('innerHTML').replace('<br>',' '),
                
            }
            originalType=li.find('span', {'class': 'Name'}).text.strip()
            dateArray=link['date'].split('-')
            print(date)
            print(date30)
            print(link['date'])
            print(dateArray)
            if int(dateArray[1])==month and int(dateArray[2])==day and int(dateArray[0])==year\
            and ('maison' in originalType or 'pavillon' in originalType): 
                
                
                #Converts the date tag to a format
                #filter for only the dates that are in exactly one month
                

                
                pagesBlanches(link)
    # writeData.addRawData(ls_links)

    return ('success')