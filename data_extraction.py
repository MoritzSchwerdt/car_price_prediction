import os
import re
import requests
from bs4 import BeautifulSoup
from requests.cookies import RequestsCookieJar
from requests_html import HTMLSession
from dotenv import load_dotenv
import json
from datetime import datetime

folder_path = "D:\\test_mobile\\mobiledata\\370146115"
data_file_name = "data.txt"

file_path = os.path.join(folder_path, data_file_name)

with open(file_path, "r") as file:
    html_content = file.read()

soup = BeautifulSoup(html_content, "html.parser")


def extract_price(souped_html):
    # Find the span with the data-testid attribute set to "prime-price"
    price_span = souped_html.find('span', attrs={'data-testid': 'prime-price'})

    # Extract the text of the span, remove non-breaking spaces and the currency symbol
    price = price_span.text.replace('\xa0', '').replace('€', '')

    return price

def extract_technical_features(souped_html):
    # Initialize an empty dictionary to store the features
    technical_features = {}

    # Find all the feature rows in the HTML
    feature_rows = souped_html.find_all('div', class_='g-row u-margin-bottom-9')

    # Iterate over each feature row
    for row in feature_rows:
        # Find the label and value divs in the current row
        label_div = row.find('div', {'id': lambda x: x and x.endswith('-l')})
        value_div = row.find('div', {'id': lambda x: x and x.endswith('-v')})

        # If both the label and value divs were found, add the feature to the dictionary
        if label_div and value_div:
            label = label_div.get_text(strip=True)
            value = value_div.get_text(strip=True)

            # Clean up the value
            value = value.encode('utf-8').decode('unicode_escape')  # Decode Unicode escape sequences
            value = value.replace('\xa0', ' ')  # Replace non-breaking spaces with regular spaces
            value = value.replace('Â', ' ')  # Replace 'Â' with a regular space
            value = re.sub(r'\s*\([^)]*\)', '', value)  # Remove anything in parentheses
            value = value.strip()  # Remove leading/trailing whitespace

            technical_features[label] = value

    # Return the dictionary of features
    return technical_features


def extract_additional_features(souped_html):
    # Find all div elements with the class 'bullet-list'
    bullet_lists = souped_html.find_all('div', class_='bullet-list')

    # Initialize an empty list to store the features
    features = []

    # Iterate over each bullet list
    for bullet_list in bullet_lists:
        # Find all p elements in the bullet list
        p_elements = bullet_list.find_all('p')

        # Iterate over each p element
        for p in p_elements:
            # Append the text of the p element to the features list
            features.append(p.text)

    return features

def extract_description(souped_html):
    description_div = souped_html.find('div', class_='description')
    description = description_div.get_text(separator=' ')
    return description


def extract_seller_info(souped_html):
    # Find the h4 with the data-testid attribute set to "db-title"
    seller_type = souped_html.find('h4', attrs={'data-testid': 'db-title'}).text

    # Find the p with the id set to "db-address"
    address = souped_html.find('p', attrs={'id': 'db-address'}).text.replace('\\xc2\\xa0', ' ')

    # Split the address into PLZ and location, if possible
    if ' ' in address:
        plz, location = address.split(' ', 1)
    else:
        plz = address
        location = ''  # or some default value

    return seller_type, plz, location

# Now you can work with the BeautifulSoup object for data extraction or parsing
print("worked")