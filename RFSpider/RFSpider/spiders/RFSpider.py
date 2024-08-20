import sys
sys.path.append("spiders/")

import urllib.parse
import scrapy
from datetime import datetime
import ingestion_item as ii
import uuid
import json
import re
import langcodes
import os

directory = "/Users/bradc/PycharmProjects/Work/RFSpider/RFSpider/outputs"

class RFSpider(scrapy.Spider):
    name = "RFSpider"
    start_urls = ["https://www.rekhta.org/ebooks/category"]
    url_set = set()


    def start_requests(self):
        url_start = ["https://www.rekhta.org/ebooks/category"]
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

        for urls in url_start:
            yield scrapy.Request(url=urls, callback=self.parse)

    def parse(self, response):
        for link in response.css('div.imgCardLayoutTwo a::attr(href)').getall():
            yield response.follow(link, self.sub_parse)
        if response.css('li.pgNext a::attr(href)').get():
            yield response.follow(response.css('li.pgNext a::attr(href)').get(), self.parse)
    def sub_parse(self, response):
        for link in response.css('div.imgCardLayoutTwo a::attr(href)').getall():
            yield response.follow(link, self.ebook_parse)
        if response.css('li.pgNext a::attr(href)').get():
            yield response.follow(response.css('li.pgNext a::attr(href)').get(), self.sub_parse)

    def ebook_parse(self, response):
        if response.css('div.imgCardLayoutTwo a::attr(href)').getall():
            yield response.follow(response.css('li.pgNext a::attr(href)').get(), self.sub_parse)
        else:
            for links in response.css('div.ebookCard a::attr(href)').getall():
                yield response.follow(links, self.item_parse)
    def item_parse(self, response):
        if response.css('li.readMoreBtn a::attr(href)').get() in self.url_set:
            return None
        else:
            author_obj = response.css('h4:contains("Author") a::text').get()
            if author_obj:
                author_obj = author_obj.title().strip()
            editor_obj = response.css('h4:contains("Editor") a::text').get()
            if editor_obj:
                editor_obj = editor_obj.title().strip()
            title_obj = response.css('h3.ebkLstTtl::text').get().title()
            publisher_obj = response.css('h4:contains("Publisher") a::text').get()
            if publisher_obj:
                publisher_obj = publisher_obj.title().strip()
            publication_place = response.css('h4:contains("Origin")::text').get()
            if publication_place:
                publication_place = publication_place.strip()
            date_obj = response.css('h4:contains("Year of Publication")::text').get()
            if date_obj:
                date_obj = date_obj.strip()
            language_obj = response.css('h4:contains("Language :")::text').getall()
            newlang = []
            templang = []
            if language_obj:
                for item in language_obj:
                    if item.strip() != '':
                        newlang.append(item.strip().title())
                for item in newlang:
                    if ', ' in item:
                        templang = item.split(', ')
                        newlang.remove(item)
                        for item in templang:
                            newlang.append(item)
            if len(newlang) > 0:
                language_obj = newlang
            else:
                language_obj = None
            summary_obj = response.css('div.ppcmpltTxt p::text').get()
            if summary_obj:
                summary_obj = summary_obj.strip()
            all_categories = response.css('h4:contains("Categories")::text').getall()
            temp_categories = []
            categories_obj = []
            sub_categories_obj = []
            for item in all_categories:
                if item.strip() != '':
                    temp_categories.append(item.strip())
            if len(temp_categories) > 1:
                categories_obj = temp_categories[0]
                sub_categories_obj = temp_categories[1]
            elif len(temp_categories) > 0:
                categories_obj = temp_categories[0]
                sub_categories_obj = None
            else:
                categories_obj = None
                sub_categories_obj = None
            if categories_obj != None and categories_obj != []:
                if ', ' in categories_obj:
                    categories_obj = categories_obj.split(', ')
                else:
                    categories_obj = [categories_obj]
            if sub_categories_obj != None and sub_categories_obj != []:
                if ', ' in sub_categories_obj:
                    sub_categories_obj = sub_categories_obj.split(', ')
                else:
                    sub_categories_obj = [sub_categories_obj]
            page_obj = response.css('h4:contains("Pages")::text').get()
            if page_obj:
                page_obj = page_obj.strip()
            isbn_issn = response.css('h4:contains("ISBN")::text').get()
            isbn = None
            issn = None
            if isbn_issn:
                isbn_issn = isbn_issn.strip()
                issn_pattern = r'\d{4}-\d{3}[0-9Xx]'
                if re.match(issn_pattern, isbn_issn):
                    issn = isbn_issn
                    isbn = None
                else:
                    issn = None
                    isbn = isbn_issn
            contributor_obj = response.css('h4:contains("Contributor") a::text').get()
            if contributor_obj:
                contributor_obj = contributor_obj.title().strip()
            thumbnail_obj = response.css('div.ebkImgContainer img::attr(src)').get()
            link_obj = response.css('li.readMoreBtn a::attr(href)').get()

            ingestion_item = ii.IngestionItem()
            collection_item = ii.CollectionItem()
            harvest_item = ii.HarvestItem()
            file_item = ii.FileItem()
            artifact_item = ii.ArtifactItem()
            thumbnail_item = ii.ThumbnailItem()

            prop_list = []

            # Harvest Item
            harvest_item["id"] = str(uuid.uuid4())
            harvest_item["date"] = datetime.now()
            # Collection Item
            collection_item["id"] = "7d09627e-d9d8-4df5-b606-40865410a3b8"
            collection_item["organization"] = "rekhta-foundation"
            collection_item["title"] = 'eBooks'
            # Authors
            author_list = []
            if author_obj:
                author_item = ii.AuthorItem()
                author_item['name'] = author_obj
                author_item['role'] = 'Author'
                author_list.append(author_item)
            if editor_obj:
                editor_item = ii.AuthorItem()
                editor_item['name'] = editor_obj
                editor_item['role'] = 'Editor'
                author_list.append(editor_item)
            # Contributor
            if contributor_obj:
                contributor_item = ii.AuthorItem()
                contributor_item['name'] = contributor_obj
                contributor_item['role'] = 'Contributor'
                author_list.append(contributor_item)
            if len(author_list) > 0:
                artifact_item['authors'] = author_list
            # ID and Publisher
            artifact_item['id'] = str(uuid.uuid4())
            artifact_item['type'] = "book"
            if publisher_obj:
                artifact_item['publisher'] = publisher_obj
            if publication_place:
                artifact_item['publication_place'] = publication_place
            # File Item
            file_item["url"] = link_obj
            file_item["media_type"] = "text/html"
            if language_obj:
                if language_obj[0] == 'Devnagari' and len(language_obj) > 1:
                    file_item['language'] = str(langcodes.find(language_obj[1]))
                elif language_obj[0] != 'Devnagari':
                    file_item['language'] = str(langcodes.find(language_obj[0]))
            artifact_item["files"] = [file_item]
            # Languages
            language_list = []
            if language_obj:
                for items in language_obj:
                    if items == 'Devnagari':
                        script_item = ii.PropItem()
                        script_item['key'] = "Script"
                        script_item['value'] = items
                        prop_list.append(script_item)
                    else:
                        language_list.append(str(langcodes.find(items)))
            if len(language_list) > 0:
                artifact_item['languages'] = language_list
            # Series info
            artifact_item["uri"] = link_obj
            artifact_item["title"] = title_obj
            if date_obj:
                artifact_item['date_published'] = f"{date_obj}-01-01"
            if summary_obj:
                artifact_item['summary'] = summary_obj
            if isbn:
                artifact_item['isbn_online'] = isbn
            if issn:
                artifact_item['issn'] = issn
            # Thumbnail
            thumbnail_item["url"] = thumbnail_obj
            artifact_item['thumbnail'] = thumbnail_item
            # Page Number
            page_item = ii.PropItem()
            page_item['key'] = "Pages"
            if page_obj:
                page_item['value'] = page_obj
                prop_list.append(page_item)
            if len(prop_list) > 0:
                artifact_item['props'] = prop_list
            # Categories and Subcategories
            categories_list = []
            if categories_obj:
                for item in categories_obj:
                    if item == 'Others':
                        continue
                    else:
                        categories_list.append(item)
            if sub_categories_obj:
                for item in sub_categories_obj:
                    if item == 'Others':
                        continue
                    else:
                        categories_list.append(item)
            if len(categories_list) > 0:
                artifact_item['topics'] = categories_list

            ingestion_item["collection"] = collection_item
            ingestion_item["harvest"] = harvest_item
            ingestion_item["artifacts"] = [artifact_item]

            if artifact_item["uri"] and artifact_item["title"]:
                return ingestion_item
            else:
                self.logger.warning(f'{response.url} did not parse to a usable artifact')
                return None

