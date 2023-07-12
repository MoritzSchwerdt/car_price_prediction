import os
import re
import requests
import json

from bs4 import BeautifulSoup
from requests.cookies import RequestsCookieJar
from requests_html import HTMLSession
from dotenv import load_dotenv
from datetime import datetime
from pymongo import MongoClient




def extract_price(souped_html):
    # Find the span with the data-testid attribute set to "prime-price"
    price_span = souped_html.find('span', attrs={'data-testid': 'prime-price'})

    # Extract the text of the span
    price = price_span.text

    # Use regular expressions to extract only the numeric part of the price
    price = re.findall(r'\d+', price.replace('.', ''))

    # The re.findall function returns a list, so if the list is not empty, return the first element
    return price[0] if price else None

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

    # Check if the description_div is None
    if description_div is None:
        return None

    description = description_div.get_text(separator=' ')
    return description


def extract_seller_info(souped_html):
    # Find the h4 with the data-testid attribute set to "db-title"
    seller_type = souped_html.find('h4', attrs={'data-testid': 'db-title'}).text


    # Find the p with the id set to "db-address"
    address = souped_html.find('p', attrs={'id': 'db-address'}).text.replace('\\xc2\\xa0', ' ')

    info = {'street': '',
            'country': '',
            'plz': '',
            'location': '',
            'seller_type': seller_type}

    if(seller_type == 'Privatanbieter'):
        #Privatanbieter do not have Street listed
        # Define the regular expression pattern for Privatanbieter
        pattern = r'^(?P<country>[A-Z]{2})-(?P<plz>\d+)\s(?P<location>.+)$'

        # Use the pattern to search the address string
        match = re.search(pattern, address)

        # If a match was found, update the information
        if match:
            info.update(match.groupdict())
    else:
        #seller_type has to be Händler, they have Streets Listed
        # Define the regular expression pattern
        pattern = r'^(?P<street>.+?)\s*(?P<country>[A-Z]{2})-(?P<plz>\d+)\s(?P<location>.+)$'

        # Use the pattern to search the address string
        match = re.search(pattern, address)

        if match:
            info.update(match.groupdict())
    return info
def extract_image_paths(directory):
    """
    Extracts image paths from a given directory.

    Args:
    directory (str): The directory from which to extract image paths.

    Returns:
    dict: A dictionary where the keys are image names and the values are the corresponding paths.
    """
    image_paths = {}

    # Iterate over the files in the directory
    for filename in os.listdir(directory):
        # Check if the file is an image
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            # Get the path of the image
            path = os.path.join(directory, filename)

            # Add the image path to the dictionary
            image_paths[filename] = path

    return image_paths

def extract_offline_status(directory):
    """
    Extracts the offline status from a given directory.

    Args:
    directory (str): The directory from which to extract the offline status.

    Returns:
    datetime: A datetime object representing the offline status.
    """
    # Define the path to the offline_status file
    file_path = os.path.join(directory, "offline_status.txt")

    # Check if the file exists
    if os.path.exists(file_path):
        # Open the file and read the offline status
        with open(file_path, "r") as file:
            offline_status = file.read().strip()

        # Convert the offline status to a datetime object
        offline_status = datetime.strptime(offline_status, "%Y-%m-%d %H:%M:%S")

        return offline_status

    # If the file does not exist, return None
    return None


def extract_online_since(directory):
    """
    Extracts the online since date from a given directory.

    Args:
    directory (str): The directory from which to extract the online since date.

    Returns:
    datetime: A datetime object representing the online since date.
    """
    # Define the path to the online_since file
    file_path = os.path.join(directory, "online_since.txt")

    # Check if the file exists
    if os.path.exists(file_path):
        # Open the file and read the online since date
        with open(file_path, "r") as file:
            online_since = file.read().strip()

        # The online since date is in the format "Inserat online seit %d.%m.%Y, %H:%M"
        # So we need to extract the date and time from this string

        # Extract the date and time using regular expressions
        date_time = re.search(r"Inserat online seit (\d{2}.\d{2}.\d{4}), (\d{2}:\d{2})", online_since)

        # If the date and time were successfully extracted, convert them to a datetime object
        if date_time:
            date = datetime.strptime(date_time.group(1), "%d.%m.%Y")
            time = datetime.strptime(date_time.group(2), "%H:%M").time()

            # Combine the date and time into a single datetime object
            online_since = datetime.combine(date, time)

            return online_since

    # If the file does not exist, or the date and time could not be extracted, return None
    return None

def extract_data(directory, id, souped_html):
    """
    Extracts data from the given BeautifulSoup object and directory.

    Args:
    souped_html (BeautifulSoup): The BeautifulSoup object to extract data from.
    directory (str): The directory from which to extract image paths.

    Returns:
    dict: A dictionary containing the extracted data.
    """
    # Extract the data
    price = extract_price(souped_html)
    technical_features = extract_technical_features(souped_html)
    additional_features = extract_additional_features(souped_html)
    description = extract_description(souped_html)
    street, country, plz, location, seller_type,  = extract_seller_info(souped_html).values()
    image_paths = extract_image_paths(directory)
    offline_status = extract_offline_status(directory)
    online_since = extract_online_since(directory)

    # Combine the data into a dictionary
    data = {
        '_id': id,
        'price': price,
        'technical_features': technical_features,
        'additional_features': additional_features,
        'description': description,
        'seller_info': {
            'type': seller_type,
            'country': country,
            'street': street,
            'plz': plz,
            'location': location
        },
        'image_paths': image_paths,
        'offline_status': offline_status,
        'online_since': online_since
    }

    # Return the dictionary
    return data

def iterate_mobile_folder(data_directory):
    data_file_name = "data.txt"


    for dirName, subdirList, _ in os.walk(data_directory):
        for subdir in subdirList:
            full_path = os.path.join(dirName, subdir)
            file_path = os.path.join(full_path, data_file_name)

            with open(file_path, "r") as file:
                html_content = file.read()

            soup = BeautifulSoup(html_content, "html.parser")

            try:
                extracted = extract_data(full_path, subdir, soup)

                print(f"inserted {subdir}")


                collection.insert_one(extracted)
            except:
                print(f"exception in {subdir}")

def soupe_up_by_path(data_file):

    with open(data_file, "r") as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, "html.parser")

    return soup


#folder_path = "D:\\test_mobile\\mobiledata"

folder_path = "D:\\test_mobile\\mobiledata"
#test = soupe_up_by_path("D:\\test_mobile\\mobiledata\\299581656\\data.txt")

#test_data = extract_data(folder_path, "299581656", test)
# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')

# Select the database and collection
db = client['mobile']
collection = db['bmw']


iterate_mobile_folder(folder_path)








# Insert the data into the collection
#collection.insert_one(first)



# Now you can work with the BeautifulSoup object for data extraction or parsing
print("worked")