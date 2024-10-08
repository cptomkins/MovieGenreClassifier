from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from constants import *
import pandas as pd
import re


def is_load_more_button(text):
    pattern = r'(\d+) more'
    
    match = re.search(pattern, text)
    
    if match:
        return int(match.group(1))
    else:
        return None


def load_more(iterations=19):
    
    quantity_id = driver.find_elements(By.CLASS_NAME, 'sc-13add9d7-3.fwjHEn')[0]
    max_results = int(quantity_id.text.split(' of ')[-1].replace(',', ''))
    expected_quantity = 50 + (50 * iterations)

    if expected_quantity > max_results:
        expected_quantity = max_results
        add_one = max_results % 50 != 0
        iterations = (max_results - 50) // 50 + add_one

    for i in range(iterations):

        buttons = driver.find_elements(By.TAG_NAME, 'button')
        load_more_button = None
        buttons.reverse()
        for button in buttons:
            number_to_load = is_load_more_button(button.text)
            if number_to_load:
                load_more_button = button
                break

        if not load_more_button:
            raise RuntimeError('No load more button found.')

        print(f'Loading {number_to_load} more results... ({i})')
        driver.execute_script("arguments[0].click();", load_more_button)

        time.sleep(5)

    return expected_quantity


# Set up Selenium WebDriver (using Chrome in this example)
driver = webdriver.Chrome()

url_template = 'https://www.imdb.com/search/title/?genres={genre}&explore=genres'

genre_data = []
errored = False
warnings = []

for genre in MOVIE_GENRES:
    url = url_template.format(genre=genre)
    driver.get(url)
    time.sleep(1.5)
    
    print('\nMOVIE GENRE: {}\n'.format(genre))

    expected_quantity = load_more()

    elements = driver.find_elements(By.CLASS_NAME, 'ipc-metadata-list-summary-item')
    quantity = len(elements)
    print('Discovered', quantity, 'movies.')

    if quantity != expected_quantity:
        errored=True
        error_message = f'Unexpected number of elements {quantity} (expected {expected_quantity}) for genre {genre}.'
        break

    for element in elements:
        img_elements = element.find_elements(By.TAG_NAME, 'img')
        if not img_elements:
            warnings.append('WARNING: Image not found: {}'.format(element.text))
            continue
        img_element=img_elements[0]
        img_src = img_element.get_attribute('src')
        img_alt = img_element.get_attribute('alt')

        genre_data.append((genre, img_src))

df = pd.DataFrame(genre_data, columns=['genre', 'img_src'])

print(df.head())

# Save DataFrame to CSV
df.to_csv('genre_data_2.csv', index=False)

if warnings:
    print('Code finished with warnings:')
    for warning in warnings:
        print('WARNING: {}'.format(warning))

if errored:
    raise RuntimeError(error_message)

driver.quit()
