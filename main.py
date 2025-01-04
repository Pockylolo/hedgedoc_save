import os
import re
from time import sleep

import requests
from dotenv import load_dotenv

# Configuration
load_dotenv()
hedgedoc_base_url = "https://hedgedoc.cri.epita.fr"
notes_list_url = f"{hedgedoc_base_url}/history"
download_url_template = f"{hedgedoc_base_url}/{{note_id}}/download"
local_save_path = "./backup_notes"
session_cookie = {
    "connect.sid": os.getenv("CONNECT_SID")
}
sleep_time = 5  # time between each note download


def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


def download_image(url, save_path):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(response.content)
    except requests.RequestException as e:
        print(f"Error saving image {url}: {e}")


def extract_image_urls(markdown_text):
    image_pattern = r"!\[.*?\]\((https?://[^\s\)]+)\)"
    return re.findall(image_pattern, markdown_text)


def save_note(note_id, note_title):
    markdown_url = download_url_template.format(note_id=note_id)
    response = requests.get(markdown_url, cookies=session_cookie)

    if response.status_code != 200:
        print(f"Error getting note {note_title}")
        return

    markdown_text = response.text
    note_folder = os.path.join(local_save_path, note_title)
    create_folder(note_folder)

    markdown_file = os.path.join(note_folder, f"{note_title}.md")
    with open(markdown_file, "w", encoding="utf-8") as f:
        f.write(markdown_text)

    # Save HTML
    html_content = requests.get(f"{hedgedoc_base_url}/note/{note_id}", cookies=session_cookie).text
    html_file = os.path.join(note_folder, f"{note_id}.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Save images
    image_urls = extract_image_urls(markdown_text)
    for img_url in image_urls:
        img_name = os.path.basename(img_url)
        img_path = os.path.join(note_folder, img_name)
        download_image(img_url, img_path)


def fetch_and_save_all_notes():
    response = requests.get(notes_list_url, cookies=session_cookie)
    if response.status_code != 200:
        print("Cannot fetch notes list")
        return

    notes = response.json()["history"]
    for note in notes:
        note_id = note["id"]
        note_title = note["text"]
        print(f"Saving note : {note_title}...")
        save_note(note_id, note_title)
        sleep(sleep_time)


if __name__ == "__main__":
    create_folder(local_save_path)
    fetch_and_save_all_notes()
