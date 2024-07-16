import requests
import re
from bs4 import BeautifulSoup
import json
import os
import base64
from PIL import Image
from io import BytesIO
import time
import random
import string
import shutil

# Define the URL and headers
url = "https://algeria.blsspainglobal.com/DZA/CaptchaPublic/GenerateCaptcha?data=YUwscxhVdDMB3uhl06lPCs7tpUXE93SnZsOQTUBftoVhwqt1TzamKdeT1OGEYg9ynAuktlIUscxX8t5LgQ5dmUZzsOnGSuJsjYXfqZKr1w0%3d"
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "cookie": ".AspNetCore.Antiforgery.cyS7zUT4rj8=CfDJ8G5WDp_IrNVKvwWVBRKmnBWhPkZ326sKsEE2J5itHasPGc0EsM2Cl6bIOsUVYDsO_Bq3EJBcWeddoW0w2d9LxVDOwwoGCHK842DNS2g8gj_hrAW3CLqz1TNjlcKgXmHK059jduLCibFvqWR4yLq5aEM",
    "pragma": "no-cache",
    "referer": "https://algeria.blsspainglobal.com/DZA/account/login",
    "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="104"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "iframe",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (X11; CrOS aarch64 13597.84.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.105 Safari/537.36"
}

def generate_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

def process_files(data):
    for item in data.split("data/")[1:]:
        file_name, number = item.split(": ")
        number = number.strip()
        new_file_name = f"{number}({generate_random_string()}).png"
        new_folder = number

        os.makedirs(new_folder, exist_ok=True)

        old_path = os.path.join("data", file_name.replace('.gif', '.png'))
        new_path = os.path.join(new_folder, new_file_name)

        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            print(f"Renamed and moved {file_name.replace('.gif', '.png')} to {new_path}")
        else:
            print(f"File {old_path} does not exist")

def clear_directory_contents(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            os.remove(os.path.join(root, file))
        for dir in dirs:
            shutil.rmtree(os.path.join(root, dir))

def save_html_content(response, filename="1.html"):
    with open(filename, "wb") as file:
        file.write(response.content)
    print(f"Response saved to {filename}")

def parse_images_from_html(filename="1.html"):
    with open(filename, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'lxml')

    images = soup.find_all('img', src=lambda x: x and x.startswith('data:image'))
    image_data = {}
    for img in images:
        img_src = img['src']
        onclick_attr = img.get('onclick', '')
        match = re.search(r"Select\('([^']+)'", onclick_attr)
        img_id = match.group(1) if match else 'no-id'
        image_data[img_id] = img_src
    return image_data

def save_images_to_disk(image_data, output_folder='data'):
    os.makedirs(output_folder, exist_ok=True)
    for img_id, img_data in image_data.items():
        if img_data.startswith('data:image'):
            base64_str = img_data.split(';base64,')[-1]
            img_bytes = base64.b64decode(base64_str)
            img = Image.open(BytesIO(img_bytes))
            img_filename = os.path.join(output_folder, f"{img_id}.png")
            img.save(img_filename, format='PNG')
            print(f"Saved image {img_id}.png")

def send_data(endpoint, data, delay=0):
    time.sleep(delay)
    response = requests.post(endpoint, json=data, headers={"Content-Type": "application/json"})
    if response.status_code == 200:
        print("Data sent successfully.")
        print("Received Data:")
        print(response.json())
    else:
        print(f"Failed to send data. Status code: {response.status_code}")

def fetch_and_process_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get("data", "")
        process_files(data)
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")

while True:
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            save_html_content(response)
        else:
            print(f"Request failed with status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")

    image_data = parse_images_from_html()
    with open('images.json', 'w', encoding='utf-8') as json_file:
        json.dump(image_data, json_file, ensure_ascii=False, indent=4)
    print(f"Extracted {len(image_data)} images and saved to images.json")

    with open('images.json', 'r') as f:
        data = json.load(f)

    save_images_to_disk(data)
    print("Images saved successfully.")

    send_data("https://ee9e-34-19-25-14.ngrok-free.app/receive_data", data)

    fetch_and_process_data("https://ee9e-34-19-25-14.ngrok-free.app/data")

    clear_directory_contents("data")
    print("All contents of the 'data' directory have been removed.")

    time.sleep(1)
