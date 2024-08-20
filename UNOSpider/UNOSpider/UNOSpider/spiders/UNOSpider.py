import sys
sys.path.append("spiders/")

import urllib.parse
import scrapy
from datetime import datetime
import uuid
import json
import re
import ingestion_item as ii
import urllib.parse
import maya



class UNOSpider(scrapy.Spider):
    name = 'UNOSpider'
    start_urls = ['https://digitalcommons.unomaha.edu/kabultimes/index.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.2.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.3.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.4.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.5.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.6.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.7.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.8.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.9.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.10.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.11.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.12.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.13.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.14.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.15.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.16.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.17.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.18.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.19.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.20.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.21.html', 'https://digitalcommons.unomaha.edu/kabultimes/index.22.html']



    def parse(self, response):
        for link in response.css('p.article-listing a::attr(href)').getall():
            yield response.follow(link, self.parse_document, meta={'link': link})

    def parse_document(self, response):
        thum_io_base = 'https://image.thum.io/get/auth/9343-a2bf76236ec823c6ceaaf37cc591f4c5/fullpage/width/400/png/noanimate/?url='

        ingestion_item = ii.IngestionItem()
        collection_item = ii.CollectionItem()
        harvest_item = ii.HarvestItem()
        file_item = ii.FileItem()
        artifact_item = ii.ArtifactItem()
        thumbnail_item = ii.ThumbnailItem()

        link_obj = response.meta.get('link')
        pdf_obj = response.xpath('//meta[@name="bepress_citation_pdf_url"]/@content').getall()
        date_obj = response.css('div#publication_date.element p::text').get()
        title_obj = response.css('div#title.element ::text').getall()
        new_string = ""
        for item in title_obj:
            new_string += item
        title_obj = new_string.replace('\n', '').replace('Title', '')
        thumbnail_url = thum_io_base + urllib.parse.quote_plus(link_obj)
        thumbnail_item['url'] = thumbnail_url
        artifact_item['thumbnail'] = thumbnail_item
        # Harvest Item
        harvest_item["id"] = str(uuid.uuid4())
        harvest_item["date"] = datetime.now()
        # Collection Item
        collection_item["id"] = '97f1f603-63ee-4dcd-b8e7-cecb44c29c0d'
        collection_item["title"] = 'Kabul Times'
        collection_item["organization"] = 'university-of-nebraska-at-omaha-us'
        # ID and Publisher
        artifact_item['id'] = str(uuid.uuid4())
        artifact_item['type'] = 'other'
        artifact_item['publisher'] = 'Bakhtar News Agency'
        artifact_item['publication_place'] = 'Afghanistan'
        # File Item
        pdf_items = []
        for pdfs in pdf_obj:
            file_item = ii.FileItem()
            file_item["url"] = pdfs
            file_item["media_type"] = "application/pdf"
            file_item['languages'] = ["en"]
            pdf_items.append(file_item)
            artifact_item["files"] = pdf_items
        # Series Info
        artifact_item["uri"] = link_obj
        artifact_item["title"] = title_obj
        artifact_item["series"] = "Kabul Times"
        date_parts = date_obj.split("-")

        new_date_parts = []
        if len(date_parts) == 3:
            new_date_parts.append(date_parts[2])
            if len(str(date_parts[0])) < 2:
                new_date_parts.append(f'0{date_parts[0]}')
            else:
                new_date_parts.append(date_parts[0])
            if len(str(date_parts[1])) < 2:
                new_date_parts.append(f'0{date_parts[1]}')
            else:
                new_date_parts.append(date_parts[1])

        if len(date_parts) == 2:
            new_date_parts.append(date_parts[1])
            if len(str(date_parts[0])) < 2:
                new_date_parts.append(f'0{date_parts[0]}')
            else:
                new_date_parts.append(date_parts[0])
            new_date_parts.append('01')

        if len(date_parts) == 1:
            new_date_parts.append(date_parts[0])
            new_date_parts.append('01')
            new_date_parts.append('01')

        date_published = '-'.join(new_date_parts)
        artifact_item['date_published'] = date_published

        ingestion_item["collection"] = collection_item
        ingestion_item["harvest"] = harvest_item
        ingestion_item["artifacts"] = [artifact_item]


        if artifact_item["uri"] and artifact_item["title"]:
            return ingestion_item
        else:
            self.logger.warning(f'{response.url} did not parse to a usable artifact')
            return None


