import requests
from bs4 import BeautifulSoup
import writeData
session = requests.Session()
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
url_pages_blanches = 'https://www.pagesjaunes.fr/pagesblanches/recherche?ou='

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()


def pagesBlanches(ls_links):
        # check in phone book
    if 'street' in ls_links:
        pages_blanches_address = ' '.join([ls_links['street'],
                                           ls_links['postalCode'],
                                           ls_links['city']])
    else:
        pages_blanches_address = ' '.join([ls_links['location'],
                                           ls_links['city'],
                                           ls_links['department']])
    driver.get(f"{url_pages_blanches}{pages_blanches_address}")
    return 0