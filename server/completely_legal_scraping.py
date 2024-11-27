import os
import logging
from scrapy.crawler import CrawlerProcess
from scrapy import Spider, Request
from scrapy.pipelines.images import ImagesPipeline
from urllib.parse import urljoin
from PIL import Image

# Configuration
DOWNLOAD_DIR = 'downloaded_images'
LOG_LEVEL = 'DEBUG'
COMPRESSION_QUALITY = 85  # JPEG quality for compression (1-95)

class WikimediaImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        """Generate Requests for the image URLs."""
        for image_url in item.get('image_urls', []):
            yield Request(image_url, meta={'item': item})

    def file_path(self, request, response=None, info=None, *, item=None):
        """Customize the file path where the image will be saved."""
        image_name = item.get('image_name', '')
        return f"{image_name}"

    def item_completed(self, results, item, info):
        """Handle post-processing after the image is downloaded."""
        if results and results[0][0]:
            path = results[0][1]['path']
            full_path = os.path.join(self.store.basedir, path)
            self.compress_image(full_path)
            item['local_path'] = full_path
        else:
            logging.error(f"Failed to download image {item.get('image_name')}")
            item['local_path'] = None
        return item

    def compress_image(self, image_path):
        """Compress the image to reduce file size."""
        try:
            with Image.open(image_path) as img:
                img = img.convert('RGB')  # Ensure compatibility
                img.save(image_path, 'JPEG', quality=COMPRESSION_QUALITY)
        except Exception as e:
            logging.error(f"Error compressing image {image_path}: {e}")
            os.remove(image_path)

class WikimediaSpider(Spider):
    name = 'wikimedia_spider'
    allowed_domains = ['commons.wikimedia.org']
    start_urls = ['https://commons.wikimedia.org/wiki/Category:Featured_pictures_on_Wikimedia_Commons']
    custom_settings = {
        'ITEM_PIPELINES': {'__main__.WikimediaImagePipeline': 1},
        'IMAGES_STORE': DOWNLOAD_DIR,
        'LOG_LEVEL': LOG_LEVEL,
        'USER_AGENT': 'Mozilla/5.0 (compatible; ImageScraper/1.0)',
        'HTTPCACHE_ENABLED': True,
        'HTTPCACHE_EXPIRATION_SECS': 0,
        'HTTPCACHE_DIR': 'httpcache',
        'HTTPCACHE_IGNORE_HTTP_CODES': [],
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image_count = 0
        self.max_images = 10  # Adjust as needed

    def parse(self, response):
        """Parse the category page and follow links to image pages."""
        # Updated selector to match current page structure
        image_pages = response.css('div#mw-content-text div.gallery a::attr(href)').getall()
        logging.debug(f"Found {len(image_pages)} image page links.")
        for link in image_pages:
            url = urljoin(response.url, link)
            yield Request(url, callback=self.parse_image_page)

        # Follow next page links
        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_image_page(self, response):
        """Parse individual image pages to extract image URLs and metadata."""
        # Updated selector to match current page structure
        image_url = response.css('div.fullMedia a::attr(href)').get()
        if image_url:
            image_url = urljoin(response.url, image_url)
            logging.debug(f"Extracted image URL: {image_url}")
            image_name = os.path.basename(image_url)
            item = {
                'image_urls': [image_url],  # 'image_urls' must be a list
                'image_name': image_name,
                'page_url': response.url,
            }
            if self.image_count < self.max_images:
                self.image_count += 1
                logging.debug(f"Yielding item for image: {image_name}")
                yield item
            else:
                return
        else:
            logging.warning(f"No image URL found on page: {response.url}")

def main():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    process = CrawlerProcess()
    process.crawl(WikimediaSpider)
    process.start()

if __name__ == "__main__":
    main()
