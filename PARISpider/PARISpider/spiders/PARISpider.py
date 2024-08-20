import sys
sys.path.append("spiders/")

import urllib.parse
import scrapy
from datetime import datetime
import ingestion_item as ii
import uuid
import json
import re
from datetime import date
import os

directory = "/Users/bradc/PycharmProjects/Work/PARISpider/PARISpider/outputs/"


class PARISpider(scrapy.Spider):
    name = "PARISpider"
    start_urls = ["https://ruralindiaonline.org/en/gallery/categories/audiozone/", "https://ruralindiaonline.org/en/gallery/categories/videozone/"]
    url_set = set()


    def start_requests(self):
        url_start = ["https://ruralindiaonline.org/en/gallery/categories/audiozone/", "https://ruralindiaonline.org/en/gallery/categories/videozone/"]
        if not os.path.exists(directory):
            print(f"The directory '{directory}' does not exist.")
        for root, dirs, files in os.walk(directory):
            for file in files:
                # Check if the file has a JSON extension
                if not file.endswith(".json"):
                    continue
                # Full path to the JSON file
                file_path = os.path.join(root, file)
                # Open and load the JSON file
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON in file '{file_path}': {e}")
                        continue
                    print(file_path)
                    for item in data:
                        for artifact in item['artifacts']:
                            url = artifact["uri"]
                            self.url_set.add(url)

        print('URL' + str(len(self.url_set)))
        for items in self.url_set:
            print(items)
        for urls in url_start:
            yield scrapy.Request(url=urls, callback=self.parse)

    def parse(self, response):

        if response.css("h1.title-light::text").get() == "AudioZone":
            for items in response.css('div.caption a::attr(href)').getall():
                link = urllib.parse.urljoin("https://ruralindiaonline.org/", items)
                if "articles" in items:
                    if link in self.url_set:
                        continue
                    else:
                        thumbnail = urllib.parse.urljoin("https://ruralindiaonline.org/",
                                                 response.css('img.img-responsive::attr(src)').get())
                        yield response.follow(link, self.audio_parse, meta={'thumbnail': thumbnail})
            if response.xpath('//li[contains(@class, "page-nav")]/a[contains(i/@class, "fa-angle-right")]/@href').get() != None:
                next_page = urllib.parse.urljoin("https://ruralindiaonline.org/en/gallery/categories/audiozone/",
                                                 response.xpath('//li[contains(@class, "page-nav")]/a[contains(i/@class, "fa-angle-right")]/@href').get())
                yield response.follow(next_page, self.parse)
        elif response.css("h1.title-light::text").get() == "VideoZone":
            for items in response.css('div.caption a::attr(href)').getall():
                link = urllib.parse.urljoin("https://ruralindiaonline.org/", items)
                if "articles" in items:
                    if link in self.url_set:
                        continue
                    else:
                        thumbnail = urllib.parse.urljoin("https://ruralindiaonline.org/",
                                                 response.css('img.img-responsive::attr(src)').get())
                        yield response.follow(link, self.video_parse, meta={'thumbnail': thumbnail})
            if response.xpath('//li[contains(@class, "page-nav")]/a[contains(i/@class, "fa-angle-right")]/@href').get() != None:
                next_page = urllib.parse.urljoin("https://ruralindiaonline.org/en/gallery/categories/videozone/",
                                                 response.xpath('//li[contains(@class, "page-nav")]/a[contains(i/@class, "fa-angle-right")]/@href').get())
                yield response.follow(next_page, self.parse)

    def audio_parse(self, response):
        ingestion_item = ii.IngestionItem()
        collection_item = ii.CollectionItem()
        harvest_item = ii.HarvestItem()
        file_item = ii.FileItem()
        prop_item = ii.PropItem()
        artifact_item = ii.ArtifactItem()
        thumbnail_item = ii.ThumbnailItem()

        title_obj = response.xpath('//meta[@property="og:title"]/@content').get()
        date_obj = ''
        if response.xpath('//meta[@property="og:published_time"]/@content').get() != None:
            date_obj = response.xpath('//meta[@property="og:published_time"]/@content').get().split("T")[0]
        description_obj = response.xpath('//meta[@name="description"]/@content').get()
        thumbnail_obj = response.xpath('//meta[@property="og:image"]/@content').get()
        keywords_list = response.xpath('//meta[@name="keywords"]/@content').get().rstrip(', ')
        location_obj = ''
        if response.css('span.map-top-title::text').get() != None and response.css('span[itemprop="contentLocation"] span[itemprop="name"]::text').get() != None:
            location_obj = response.css('span.map-top-title::text').get().replace('\n', '') + \
                           response.css('span[itemprop="contentLocation"] span[itemprop="name"]::text').getall()[-1].replace('\n', '')
        authors_list = []
        for items in response.css('div.author-name::text').getall():
            author_item = ii.AuthorItem()
            if ":" in items:
                items = items.split(":")
                author_item['name'] = items[1].replace('\n', '').title().strip()
            else:
                author_item['name'] = items.replace('\n', '').title().strip()
            if " And " in author_item['name']:
                names = author_item['name'].split(" And ")
                for name in names:
                    author_item = ii.AuthorItem()
                    author_item['name'] = name.title().strip()
                    authors_list.append(author_item)
            elif author_item['name'] != "":
                authors_list.append(author_item)
        for items in response.css('div.author-name span::text').getall():
            author_item = ii.AuthorItem()
            if ":" in items:
                items = items.split(":")
                author_item['name'] = items[1].replace('\n', '').title().strip()
            else:
                author_item['name'] = items.replace('\n', '').title().strip()
            if " And " in author_item['name']:
                names = author_item['name'].split(" And ")
                for name in names:
                    author_item = ii.AuthorItem()
                    author_item['name'] = name.title().strip()
                    authors_list.append(author_item)
            elif author_item['name'] != "":
                authors_list.append(author_item)
        artifact_item["authors"] = authors_list
        if location_obj != '':
            artifact_item["publication_place"] = location_obj
        if date_obj != '':
            artifact_item["date_published"] = date_obj
        artifact_item["title"] = title_obj
        thumbnail_item["url"] = thumbnail_obj
        artifact_item["thumbnail"] = thumbnail_item
        artifact_item["uri"] = response.url
        artifact_item["type"] = 'audio'
        if description_obj != None:
            artifact_item["summary"] = description_obj

        file_item["url"] = response.url
        file_item["media_type"] = "text/html"
        artifact_item["files"] = [file_item]

        # Harvest Item
        harvest_item["id"] = str(uuid.uuid4())
        harvest_item["date"] = datetime.now()
        # Collection Item
        collection_item["id"] = "8a05b699-5b0a-4b2d-b386-56603d62361d"
        collection_item["title"] = "People’s Archive of Rural India - AudioZone"
        collection_item["organization"] = "the-countermedia-trust"
        # ID and Publisher
        artifact_item['id'] = str(uuid.uuid4())

        ingestion_item["collection"] = collection_item
        ingestion_item["harvest"] = harvest_item
        ingestion_item["artifacts"] = [artifact_item]

        if artifact_item["uri"] and artifact_item["title"]:
            return ingestion_item
        else:
            self.logger.warning(f'{response.url} did not parse to a usable artifact')
            return None

    def video_parse(self, response):
        ingestion_item = ii.IngestionItem()
        collection_item = ii.CollectionItem()
        harvest_item = ii.HarvestItem()
        file_item = ii.FileItem()
        prop_item = ii.PropItem()
        artifact_item = ii.ArtifactItem()
        thumbnail_item = ii.ThumbnailItem()

        title_obj = response.xpath('//meta[@property="og:title"]/@content').get()
        date_obj = ''
        if response.xpath('//meta[@property="og:published_time"]/@content').get() != None:
            date_obj = response.xpath('//meta[@property="og:published_time"]/@content').get().split("T")[0]
        description_obj = response.xpath('//meta[@name="description"]/@content').get()
        thumbnail_obj = response.xpath('//meta[@property="og:image"]/@content').get()
        keywords_list = response.xpath('//meta[@name="keywords"]/@content').get().rstrip(', ')
        location_obj = ''
        if response.css('span.map-top-title::text').get() != None and response.css('span[itemprop="contentLocation"] span[itemprop="name"]::text').get() != None:
            location_obj = response.css('span.map-top-title::text').get().replace('\n', '') + \
                           response.css('span[itemprop="contentLocation"] span[itemprop="name"]::text').getall()[-1].replace('\n', '')
        authors_list = []
        for items in response.css('div.author-name::text').getall():
            author_item = ii.AuthorItem()
            if ":" in items:
                items = items.split(":")
                author_item['name'] = items[1].replace('\n', '').title().strip()
            else:
                author_item['name'] = items.replace('\n', '').title().strip()
            if " And " in author_item['name']:
                names = author_item['name'].split(" And ")
                for name in names:
                    author_item = ii.AuthorItem()
                    author_item['name'] = name.title().strip()
                    authors_list.append(author_item)
            elif author_item['name'] != "":
                authors_list.append(author_item)
        for items in response.css('div.author-name span::text').getall():
            author_item = ii.AuthorItem()
            if ":" in items:
                items = items.split(":")
                author_item['name'] = items[1].replace('\n', '').title().strip()
            else:
                author_item['name'] = items.replace('\n', '').title().strip()
            if " And " in author_item['name']:
                names = author_item['name'].split(" And ")
                for name in names:
                    author_item = ii.AuthorItem()
                    author_item['name'] = name.title().strip()
                    authors_list.append(author_item)
            elif author_item['name'] != "":
                authors_list.append(author_item)
        artifact_item["authors"] = authors_list
        if location_obj != '':
            artifact_item["publication_place"] = location_obj
        if date_obj != '':
            artifact_item["date_published"] = date_obj
        artifact_item["title"] = title_obj
        thumbnail_item["url"] = thumbnail_obj
        artifact_item["thumbnail"] = thumbnail_item
        artifact_item["uri"] = response.url
        artifact_item["type"] = 'video'
        if description_obj != None and description_obj != "":
            artifact_item["summary"] = description_obj

        file_item["url"] = response.url
        file_item["media_type"] = "text/html"
        artifact_item["files"] = [file_item]

        # Harvest Item
        harvest_item["id"] = str(uuid.uuid4())
        harvest_item["date"] = datetime.now()
        # Collection Item
        collection_item["id"] = "fcb6d78d-9481-427c-a6f1-8278f72d4f5d"
        collection_item["title"] = "People’s Archive of Rural India - VideoZone"
        collection_item["organization"] = "the-countermedia-trust"
        # ID and Publisher
        artifact_item['id'] = str(uuid.uuid4())

        ingestion_item["collection"] = collection_item
        ingestion_item["harvest"] = harvest_item
        ingestion_item["artifacts"] = [artifact_item]

        if artifact_item["uri"] and artifact_item["title"]:
            return ingestion_item
        else:
            self.logger.warning(f'{response.url} did not parse to a usable artifact')
            return None





