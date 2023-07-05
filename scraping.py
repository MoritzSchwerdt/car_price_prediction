import os
import requests
from bs4 import BeautifulSoup
from requests.cookies import RequestsCookieJar
from requests_html import HTMLSession
from dotenv import load_dotenv
import json
from datetime import datetime

def create_directory(directory):
    if not os.path.exists(directory):
        os.mkdir(directory)
        print('Folder for:', directory, 'was created')

def write_to_file(file_path, content):
    with open(file_path, 'w') as file_data:
        file_data.write(content)

def download_image(image_link, file_path):
    with open(file_path, 'wb') as file:
        requested_image = requests.get(image_link)
        file.write(requested_image.content)
        print('Saved image', file_path)

def item_exists(item_id, current_working_dir):
    return item_id in os.listdir(current_working_dir)

def mark_item_offline(item_folder):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    write_to_file(os.path.join(item_folder, 'offline_status.txt'), timestamp)

def is_item_offline(item_url, session):
    try:
        response = session.get(item_url)
        response.raise_for_status()
        return False
    except Exception:
        return True

def parse_item(item, session, current_working_dir):
    online_since = item.find('span', {'class': 'u-block u-pad-top-9'}).text
    item_info = item.a
    item_id = item_info.attrs['data-listing-id']
    item_url = item_info.attrs['href']

    item_folder = os.path.join(current_working_dir, item_id)

    if item_exists(item_id, current_working_dir):
        if 'offline_status.txt' in os.listdir(item_folder):
            # This item has been marked as offline, so we skip it
            return
        elif is_item_offline(item_url, session):
            # The item is still online, mark it as offline
            mark_item_offline(item_folder)
        return

    item_raw_data = session.get(item_url)
    item_raw_souped_data = BeautifulSoup(item_raw_data.content, 'html.parser')
    item_images = item_raw_souped_data.findAll('div', {'class': 'image-gallery-wrapper'})

    create_directory(item_folder)

    write_to_file(os.path.join(item_folder, 'data.txt'), str(item_raw_data.content))
    write_to_file(os.path.join(item_folder, 'online_since.txt'), online_since)

    last_occurance_of_gallery = item_images[-1]
    for index, image in enumerate(
            last_occurance_of_gallery.findAll('div', {'class': 'gallery-img-wrapper u-flex-centerer'})):
        image_link = image.img.attrs.get('src', image.img.attrs.get('data-lazy'))
        image_name = f'{item_id}_{index}.jpg'
        download_image(image_link, os.path.join(item_folder, image_name))


def parse_mobile_site(page_index, session, current_working_dir):
    url = f'https://suchen.mobile.de/fahrzeuge/search.html?categories=Cabrio&categories=SportsCar&damageUnrepaired=NO_DAMAGE_UNREPAIRED&isSearchRequest=true&makeModelVariant1.makeId=3500&makeModelVariant1.modelGroupId=21&maxFirstRegistrationDate=2006-12-31&pageNumber={page_index}&scopeId=C&sfmr=false&sortOption.sortBy=creationTime&sortOption.sortOrder=DESCENDING'
    items_request = session.get(url)
    souped_items = BeautifulSoup(items_request.content, 'html.parser')
    found_items = souped_items.findAll('div',{'class':'cBox-body cBox-body--resultitem'})

    for item in found_items:
        parse_item(item, session, current_working_dir)


def load_cookies_from_json(session, json_file_path):
    # Load the cookies from the JSON file
    with open(json_file_path, 'r') as f:
        cookies = json.load(f)

    # Create a cookie jar
    cookie_jar = RequestsCookieJar()

    # Add each cookie to the jar
    for cookie in cookies:
        cookie_jar.set(cookie['name'], cookie['value'], domain=cookie['domain'], path=cookie['path'])

    # Use the cookie jar in the session
    session.cookies = cookie_jar

def check_items_offline(directory, session):
    # Iterate over all items in the directory
    for item_id in os.listdir(directory):
        item_folder = os.path.join(directory, item_id)
        # Check if the item is a directory
        if os.path.isdir(item_folder):
            # Check if the item has been marked as offline
            if 'offline_status.txt' in os.listdir(item_folder):
                #print(f'Item {item_id} is offline.')
                pass
            else:
                # If the item has not been marked as offline, check its status
                item_url = f'https://suchen.mobile.de/fahrzeuge/details.html?id={item_id}'
                if is_item_offline(item_url, session):
                    print(f'Item {item_id} found offline.')
                    mark_item_offline(item_folder)
                else:
                    #print(f'Item {item_id} is online.')
                    pass


def main():
    load_dotenv()
    current_working_dir = os.path.join(os.getcwd(), 'mobiledata')
    session = HTMLSession()

    load_cookies_from_json(session, 'cookies.json')

    for index in range(9, 15):
     parse_mobile_site(index, session, current_working_dir)
     print('Site', index)
    print('checking offline')

    check_items_offline(current_working_dir,session)
    print('finished checking offline')

if __name__ == "__main__":
    main()
