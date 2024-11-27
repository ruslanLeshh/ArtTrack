import os  
import sys 
import csv
import logging  
from dataclasses import dataclass, asdict  
from typing import List, Dict, Optional, Set  
from concurrent.futures import ThreadPoolExecutor, as_completed  
import requests  
from urllib.parse import urlencode  
from PIL import Image  
from io import BytesIO  


DOWNLOAD_DIR = 'images/internet-images'  
METADATA_FILE = 'absolutely_legal_metadata.csv'  # CSV file to store image metadata
COMPRESSION_QUALITY = 85  # JPEG quality for compression (1-95)

MAX_WORKERS = 8  # number of threads for concurrent downloads
MAX_IMAGES = 10  # maximum number of images to download

CATEGORY = 'Featured pictures on Wikimedia Commons'  # category to download images from
LICENSES = ['CC BY-SA 4.0', 'CC BY 4.0', 'Public domain']  # acceptable licenses
USER_AGENT = 'ArtTrackImageDownloader/1.0 (https://arttrack.com/; arttrack@gmail.com)'  # compliant user-agent


# configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'  # detailed logging format
)


@dataclass
class ImageMetadata:
    """dataclass to store metadata for each image"""
    title: str
    url: str
    descriptionurl: str
    user: str
    license: str
    attribution: str
    local_path: Optional[str] = None  # path where the image is saved


class WikimediaImageDownloader:
    """class to handle downloading images from Wikimedia Commons using the MediaWiki API"""

    def __init__(self):
        self.session = requests.Session()  # session for persistent connections
        self.session.headers.update({'User-Agent': USER_AGENT})  # set user-agent for all requests
        self.images: List[ImageMetadata] = []  # list to store image metadata
        self.downloaded_titles: Set[str] = set()  # set to store titles of already downloaded images
        self.load_existing_metadata()  # load metadata if it exists

    def load_existing_metadata(self):
        """load existing metadata from CSV to avoid re-downloading images"""
        if os.path.exists(METADATA_FILE):
            try:
                with open(METADATA_FILE, 'r', newline='', encoding='utf-8') as csvfile:  # open CSV file
                    reader = csv.DictReader(csvfile)  # create CSV reader
                    for row in reader:
                        self.downloaded_titles.add(row['title'])  # add title to the set
                logging.info(f"loaded {len(self.downloaded_titles)} already downloaded images from metadata")  # log count
            except Exception as e:
                logging.error(f"failed to load existing metadata: {e}")  # log any errors
        else:
            logging.info("no existing metadata found, starting fresh")  # log if no metadata exists

    def fetch_image_titles(self, cmcontinue: Optional[str] = None) -> Dict:
        """fetch image titles from the specified category using the MediaWiki API
        :param cmcontinue: continuation token for pagination
        :return: JSON response from the API
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
            params['cmcontinue'] = cmcontinue  # add continuation token if present

        try:
            response = self.session.get('https://commons.wikimedia.org/w/api.php', params=params)  # make GET request
            response.raise_for_status()  # raise exception for HTTP errors
            return response.json()  # return JSON response
        except requests.RequestException as e:
            logging.error(f"error fetching image titles: {e}")  # log any request exceptions
            return {}

    def fetch_image_info(self, titles: List[str]) -> Dict:
        """fetch detailed image information for a batch of titles
        :param titles: list of image titles
        :return: JSON response from the API
        """
        params = {
            'action': 'query',
            'format': 'json',
            'prop': 'imageinfo',
            'titles': '|'.join(titles),
            'iiprop': 'url|user|extmetadata',
            'iiurlwidth': 800,  # specify desired image width
        }

        try:
            response = self.session.get('https://commons.wikimedia.org/w/api.php', params=params)  # make GET request
            response.raise_for_status()  # raise exception for HTTP errors
            return response.json()  # return JSON response
        except requests.RequestException as e:
            logging.error(f"error fetching image info for titles {titles}: {e}")  # log any request exceptions
            return {}

    def process_api_response(self, data: Dict):
        """process the API response and extract image metadata
        :param data: JSON response from the API
        """
        pages = data.get('query', {}).get('pages', {})  # extract pages from response

        for page_id, page in pages.items():
            imageinfo = page.get('imageinfo', [])
            if not imageinfo:
                continue  # skip if no imageinfo present

            info = imageinfo[0]
            extmetadata = info.get('extmetadata', {})
            license_short_name = extmetadata.get('LicenseShortName', {}).get('value', '')

            if LICENSES and license_short_name not in LICENSES:
                continue  # skip images with unacceptable licenses

            title = page.get('title', '')
            if title in self.downloaded_titles:
                logging.info(f"skipping already downloaded image: {title}")  # log skipped image
                continue  # skip already downloaded images

            metadata = ImageMetadata(
                title=title,
                url=info.get('url', ''),
                descriptionurl=info.get('descriptionurl', ''),
                user=info.get('user', ''),
                license=license_short_name,
                attribution=extmetadata.get('Attribution', {}).get('value', '')
            )
            self.images.append(metadata)  # add to images list

            if len(self.images) >= MAX_IMAGES:
                break  # stop if maximum number of images reached

    def fetch_images(self):
        """fetch image metadata by iterating through API responses until MAX_IMAGES is reached"""
        cmcontinue = None

        while len(self.images) < MAX_IMAGES:
            data = self.fetch_image_titles(cmcontinue)  # fetch image titles
            if not data:
                break  # exit if no data returned

            pages = data.get('query', {}).get('categorymembers', [])
            titles = [page['title'] for page in pages if page['ns'] == 6]  # namespace 6 for files

            if not titles:
                break  # exit if no titles found

            # batch titles to avoid exceeding URL length limits
            batch_size = 10  # number of titles per batch
            for i in range(0, len(titles), batch_size):
                batch_titles = titles[i:i + batch_size]
                info_data = self.fetch_image_info(batch_titles)  # fetch image info for the batch
                if not info_data:
                    continue  # skip if no data returned
                self.process_api_response(info_data)  # process the API response

                if len(self.images) >= MAX_IMAGES:
                    break  # stop if maximum number of images reached

            cmcontinue = data.get('continue', {}).get('cmcontinue')  # get continuation token
            if not cmcontinue:
                break  # exit if no more pages

    def download_image(self, image: ImageMetadata):
        """download and save a single image, then update its local_path
        :param image: ImageMetadata object containing image details
        """
        try:
            response = self.session.get(image.url, timeout=10)  # download image with timeout
            response.raise_for_status()  # raise exception for HTTP errors

            image_content = response.content  # get image bytes
            img = Image.open(BytesIO(image_content))  # open image
            img = img.convert('RGB')  # convert to RGB to ensure compatibility

            # smart compression to ensure image size does not exceed 0.5 MB
            target_size = 500000  # target size in bytes (0.5 MB)
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=COMPRESSION_QUALITY)  # initial save
            size = buffer.tell()  # current size

            if size > target_size:
                # calculate scaling factor
                scale_factor = (target_size / size) ** 0.5  # approximate scaling factor
                new_width = max(1, int(img.width * scale_factor))  # ensure width is at least 1
                new_height = max(1, int(img.height * scale_factor))  # ensure height is at least 1
                img = img.resize((new_width, new_height), Image.ANTIALIAS)  # resize image

                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=COMPRESSION_QUALITY)  # save resized image
                size = buffer.tell()

                # adjust quality if still larger
                if size > target_size:
                    quality = max(int(COMPRESSION_QUALITY * (target_size / size)), 10)  # calculate new quality
                    buffer = BytesIO()
                    img.save(buffer, format='JPEG', quality=quality)  # save with adjusted quality

            buffer.seek(0)
            img = Image.open(buffer)  # reopen image from buffer

            local_filename = os.path.basename(image.url)  # extract filename from URL
            local_path = os.path.join(DOWNLOAD_DIR, local_filename)  # define local path

            if os.path.exists(local_path):
                logging.info(f"image already exists, skipping download: {local_filename}")  # log existing image
                image.local_path = local_path  # set existing path
                return  # skip downloading

            img.save(local_path, 'JPEG', quality=COMPRESSION_QUALITY)  # save and compress image
            image.local_path = local_path  # update metadata with local path

            logging.info(f"downloaded {local_filename}")  # log successful download
        except Exception as e:
            logging.error(f"failed to download {image.url}: {e}")  # log any download errors
            image.local_path = None  # mark as failed

    def download_all_images(self):
        """download all images concurrently using ThreadPoolExecutor"""
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # submit all download tasks
            future_to_image = {executor.submit(self.download_image, image): image for image in self.images}
            for future in as_completed(future_to_image):
                image = future_to_image[future]
                if image.local_path:
                    self.downloaded_titles.add(image.title)  # add to downloaded titles
                else:
                    logging.warning(f"image {image.title} was not downloaded successfully")  # log if not downloaded

    def save_metadata_to_csv(self):
        """save all image metadata to a CSV file"""
        try:
            with open(METADATA_FILE, 'w', newline='', encoding='utf-8') as csvfile:  # open CSV file
                fieldnames = ['title', 'url', 'descriptionurl', 'user', 'license', 'attribution', 'local_path']  # define headers
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()  # write header row

                for image in self.images:
                    writer.writerow(asdict(image))  # write image metadata as a row

            logging.info(f"metadata saved to {METADATA_FILE}")  # log successful save
        except Exception as e:
            logging.error(f"failed to save metadata to CSV: {e}")  # log any errors during save

    def run(self):
        """execute the full image downloading and metadata saving process"""
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR)  # create download directory if it doesn't exist

        logging.info(f"starting image fetch for category: {CATEGORY}")  # log start of fetching
        self.fetch_images()

        if not self.images:
            logging.error("no images found to download")  # log if no images found
            sys.exit(1)  # exit script with error

        logging.info(f"found {len(self.images)} images. starting download...")  # log number of images found
        self.download_all_images()  # download all images concurrently

        logging.info("all downloads completed. saving metadata...")  # log completion of downloads
        self.save_metadata_to_csv() 

        logging.info("process completed successfully")  # log successful completion


if __name__ == "__main__":
    downloader = WikimediaImageDownloader()  
    downloader.run()  
