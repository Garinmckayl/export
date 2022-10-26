import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import writeData
session = requests.Session()
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
url_pages_blanches = 'https://www.pagesjaunes.fr/pagesblanches/recherche?ou='




def pagesBlanches(result):
    print('check in phone book')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
        
    pages_blanches_address = ' '.join([result['street'],
                                        result['city']])
    # else:
    #     pages_blanches_address = ' '.join([ls_links['location'],
    #                                        ls_links['city'],
    #                                        ls_links['department']])
    
    driver.get(f"{url_pages_blanches}{pages_blanches_address}")

    hasDriverReponse = False

    try:
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID,
                                                                        'SEL-nbresultat')))
        hasDriverReponse = True

    except:
        return

    try:
        if not hasDriverReponse:
            WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID,
                                                                            'wording-no-responses')))
            print('No responses')
            return
    except:
        pass

    try:
        if hasDriverReponse:
            no_pages_blanches_responses = driver.find_element_by_tag_name('body').get_attribute('innerHTML').find(
                "Nous n'avons pas trouvé de résultats pour votre recherche sur PagesBlanches. Vous avez été redirigé vers PagesJaunes, le service de recherche de professionnels")
            if no_pages_blanches_responses >= 0:
                print('No pages blanches data')
                return
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

   
    result['pages_blanches_particuliers_results'] = '\n'.join(
        ls_pages_blanches_part_results)
    result['inhabitants'] = len(
        ls_pages_blanches_part_results)

    print(result)
    driver.quit()

#For Sam testing
def pagesBlanchesTest(ls_links):
    return 2
