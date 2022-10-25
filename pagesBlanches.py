import requests
from bs4 import BeautifulSoup
import writeData
session = requests.Session()

url_pages_blanches = 'https://www.pagesjaunes.fr/pagesblanches/recherche?ou='

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()


def pagesBlanches(itemList):
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
    return 0
