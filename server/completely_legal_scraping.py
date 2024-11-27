import os
import sys
import requests
import logging
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO
from typing import List, Dict

# Configuration
DOWNLOAD_DIR = 'server/absolutely_legal_downloaded_images'
METADATA_FILE = 'image_metadata.csv'
COMPRESSION_QUALITY = 85  # JPEG quality for compression (1-95)
MAX_WORKERS = 8  # Number of threads for concurrent downloads
MAX_IMAGES = 10  # Maximum number of images to download
CATEGORY = 'Featured pictures on Wikimedia Commons'  # Category to download images from
LICENSES = ['CC BY-SA 4.0', 'CC BY 4.0', 'Public domain']  # Acceptable licenses

# User-Agent configuration
USER_AGENT = 'ArtTrack/1.0 (https://arttrack.com/; arttrack@gmail.com)'

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def get_image_pages(session: requests.Session, cmcontinue: str = None) -> Dict:
    """
    Retrieve image pages from a specific category using the MediaWiki API.

    :param session: requests.Session object
    :param cmcontinue: Continue token for pagination
    :return: API response as a dictionary
    """
    params = {
        'action': 'query',
        'format': 'json',
        'list': 'categorymembers',
        'cmtitle': f'Category:{CATEGORY}',
        'cmtype': 'file',
        'cmlimit': 'max',
    }
    if cmcontinue:
        params['cmcontinue'] = cmcontinue

    response = session.get('https://commons.wikimedia.org/w/api.php', params=params)
    response.raise_for_status()
    return response.json()


def get_image_info(session: requests.Session, titles: List[str]) -> Dict:
    """
    Retrieve detailed image information, including URLs and metadata.

    :param session: requests.Session object
    :param titles: List of image titles
    :return: API response as a dictionary
    """
    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'imageinfo',
        'titles': '|'.join(titles),
        'iiprop': 'url|user|extmetadata',
        'iiurlwidth': 800,  # Adjust if you want a specific width
    }

    # Properly encode the parameters
    url = 'https://commons.wikimedia.org/w/api.php'
    response = session.get(url, params=params)
    response.raise_for_status()
    return response.json()


def fetch_images(session: requests.Session) -> List[Dict]:
    """
    Fetch image metadata from Wikimedia Commons.

    :param session: requests.Session object
    :return: List of image metadata dictionaries
    """
    images = []
    cmcontinue = None

    while len(images) < MAX_IMAGES:
        data = get_image_pages(session, cmcontinue)
        pages = data.get('query', {}).get('categorymembers', [])
        titles = [page['title'] for page in pages if page['ns'] == 6]  # Namespace 6 is for files

        if not titles:
            break

        # Split titles into batches to avoid exceeding URL length limits
        batch_size = 10  # Adjust as needed
        for i in range(0, len(titles), batch_size):
            batch_titles = titles[i:i + batch_size]
            # Retrieve image info
            info_data = get_image_info(session, batch_titles)
            pages_info = info_data.get('query', {}).get('pages', {})

            for page_id, page in pages_info.items():
                imageinfo = page.get('imageinfo', [])
                if not imageinfo:
                    continue
                info = imageinfo[0]
                extmetadata = info.get('extmetadata', {})
                license_short_name = extmetadata.get('LicenseShortName', {}).get('value', '')

                if LICENSES and license_short_name not in LICENSES:
                    continue  # Skip images without acceptable licenses

                image_data = {
                    'title': page.get('title'),
                    'url': info.get('url'),
                    'descriptionurl': info.get('descriptionurl'),
                    'user': info.get('user'),
                    'license': license_short_name,
                    'attribution': extmetadata.get('Attribution', {}).get('value', ''),
                }
                images.append(image_data)
                if len(images) >= MAX_IMAGES:
                    break

            if len(images) >= MAX_IMAGES:
                break

        cmcontinue = data.get('continue', {}).get('cmcontinue')
        if not cmcontinue:
            break

    return images


def download_and_save_image(image_data: Dict):
    """
    Download and save an image, compressing it if necessary.

    :param image_data: Dictionary containing image metadata
    """
    url = image_data['url']
    filename = os.path.basename(url)
    local_path = os.path.join(DOWNLOAD_DIR, filename)

    try:
        response = requests.get(url, headers={'User-Agent': USER_AGENT})
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        image = image.convert('RGB')  # Ensure compatibility
        image.save(local_path, 'JPEG', quality=COMPRESSION_QUALITY)
        logging.info(f"Downloaded {filename}")
        image_data['local_path'] = local_path
    except Exception as e:
        logging.error(f"Failed to download {url}: {e}")
        image_data['local_path'] = None


def save_metadata(images: List[Dict]):
    """
    Save image metadata to a CSV file.

    :param images: List of image metadata dictionaries
    """
    import csv

    fieldnames = ['title', 'url', 'descriptionurl', 'user', 'license', 'attribution', 'local_path']
    with open(METADATA_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for image_data in images:
            writer.writerow(image_data)
    logging.info(f"Metadata saved to {METADATA_FILE}")


def main():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})  # Set the User-Agent header

    images = fetch_images(session)

    if not images:
        logging.error("No images found.")
        sys.exit(1)

    logging.info(f"Found {len(images)} images. Starting download...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(download_and_save_image, images)

    # Save metadata
    save_metadata(images)

    logging.info("All tasks completed.")


if __name__ == "__main__":
    main()
