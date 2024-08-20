import sys

sys.path.append("..")
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

directory = "/Users/bradc/PycharmProjects/Work/IQBALSpider/IQBALSpider/outputs/"

class IqbalspideSpider(scrapy.Spider):
    name = "IQBALSpider"
    url_set = set()

    def start_requests(self):
        collection_books = {
            "title": "Iqbal Cyber Library - Books",
            "id": "5ce3f9a4-4dd9-4737-9ae5-4c28405a609a",
            "organization": "iqbal-academy",
            "type": "book"
        }

        collection_periodicals = {
            "title": "Iqbal Cyber Library - Periodicals",
            "id": "3f6d7d30-c20f-4455-aec3-ead88d6c9a37",
            "organization": "iqbal-academy",
            "type": "journal"
        }

        seeds = [
            {"url": "https://iqbalcyberlibrary.net/en/listbooks/listbytitle.php", "collection": collection_books},
            {"url": "https://iqbalcyberlibrary.net/en/listperiodicals/iqbalreview.php",
             "collection": collection_periodicals},
            {"url": "https://iqbalcyberlibrary.net/en/listperiodicals/iqbaliyatur.php",
             "collection": collection_periodicals},
            {"url": "https://iqbalcyberlibrary.net/en/listperiodicals/iqbaliyatper.php",
             "collection": collection_periodicals},
            {"url": "https://iqbalcyberlibrary.net/en/listperiodicals/iqbaliyatar.php",
             "collection": collection_periodicals},
            {"url": "https://iqbalcyberlibrary.net/en/listperiodicals/iqbaliyattr.php",
             "collection": collection_periodicals},
            {"url": "https://iqbalcyberlibrary.net/en/listperiodicals/iqbalquarterly.php",
             "collection": collection_periodicals},
            {"url": "https://iqbalcyberlibrary.net/en/listperiodicals/periodicalsothers.php",
             "collection": collection_periodicals}
        ]
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
                    for item in data:
                        for artifact in item['artifacts']:
                            url = artifact["uri"]
                            self.url_set.add(url)

        for seed in seeds:

            url = seed["url"]
            if seed["collection"] == collection_books:
                yield scrapy.Request(url=url, callback=self.parse, meta=collection_books)
            if seed["collection"] == collection_periodicals:
                yield scrapy.Request(url=url, callback=self.parse, meta=collection_periodicals)

    def parse(self, response):
        collection = {
        "title": response.meta.get("title"),
        "id": response.meta.get("id"),
        "organization": response.meta.get("organization"),
        "type": response.meta.get("type")
        }
        for row in response.css('tr.table-row'):
            link = row.css('td:nth-child(1) a::attr(href)').get().replace("http", "https")
            if link in self.url_set:
                continue
            else:
                yield response.follow(link, self.item_parse, meta=collection)

    def item_parse(self, response):
        series_title = response.meta.get("title")
        id = response.meta.get("id")
        organization = response.meta.get("organization")
        type = response.meta.get("type")

        parallel_title = response.css('td strong:contains("Parallel Title") + td::text').get()
        title = response.css('h3.tittle::text').get()
        title_obj = parallel_title if parallel_title else title.strip()
        author_obj = response.xpath("//td[strong[text() = 'Author:']]/following-sibling::td[1]//text()").get()
        city_obj = response.xpath("//td[strong[text() = 'City:']]/following-sibling::td[1]//text()").get()
        editor_obj = response.xpath("//td[strong[text() = 'Editor:']]/following-sibling::td[1]//text()").get()
        publisher_obj =  response.xpath("//td[strong[text() = 'Publisher:']]/following-sibling::td[1]//text()").get()
        summary_obj = response.xpath("//td[strong[text() = 'Note:']]/following-sibling::td[1]//text()").getall()
        new_summary = ""
        if summary_obj:
            for item in summary_obj:
                new_summary = new_summary + item.strip().replace("\n", "").replace("\t", "")
            summary_obj = new_summary
        ddc_obj = response.xpath(
            "//td[strong[text() = 'Classification (DDC):']]/following-sibling::td[1]//text()").get()
        iap_obj = response.xpath(
            "//td[strong[text() = 'Classification (IAP):']]/following-sibling::td[1]//text()").get()
        year_obj = response.xpath("//td[strong[text() = 'Year:']]/following-sibling::td[1]//text()").get()
        pages_obj = response.xpath("//td[strong[text() = 'Pages:']]/following-sibling::td[1]//text()").get()
        subjects = response.xpath("//td[strong[text() = 'Subject:']]/following-sibling::td[1]//text()").get()
        if subjects:
            subjects = [subject.strip() for subject in subjects.split(", ")]
        language_obj = response.xpath("//td[strong[text() = 'Language:']]/following-sibling::td[1]//text()").get()
        if language_obj and language_obj != "Kashar" and language_obj != "Brahvi":
            language_obj = langcodes.find(language_obj.strip())
        else:
            language_obj = None
        if response.css('aside.col-lg-12 a::attr(href)').get():
            pdf_obj = urllib.parse.urljoin("https://iqbalcyberlibrary.net", response.css('aside.col-lg-12 a::attr(href)').get().replace("..", ""))
        else:
            pdf_obj = None
        isbn_obj = response.xpath("//td[strong[text() = 'ISBN:']]/following-sibling::td[1]//text()").get()
        thumbnail_obj = response.css("div.blog_info_left_grid img::attr(src)").get().replace("http", "https")

        ingestion_item = ii.IngestionItem()
        collection_item = ii.CollectionItem()
        harvest_item = ii.HarvestItem()
        file_item = ii.FileItem()
        author_item = ii.AuthorItem()
        artifact_item = ii.ArtifactItem()
        thumbnail_item = ii.ThumbnailItem()

        harvest_item["id"] = str(uuid.uuid4())
        harvest_item["date"] = datetime.now()
        # Collection Item
        collection_item["id"] = id
        collection_item["title"] = series_title
        artifact_item["type"] = type
        collection_item["organization"] = organization
        # ID and Publisher
        artifact_item['id'] = str(uuid.uuid4())
        if publisher_obj:
            artifact_item['publisher'] = publisher_obj
        # Thumbnail
        if thumbnail_obj:
            thumbnail_item["url"] = thumbnail_obj
            artifact_item['thumbnail'] = thumbnail_item
        # Author
        author_list = []
        if author_obj and author_obj != "Several Authors (Compilation)":
            author_item["name"] = author_obj
            author_item["role"] = 'Author'
        if editor_obj:
            author_item["name"] = editor_obj
            author_item["role"] = 'Editor'
        if len(author_list) > 0:
            artifact_item["authors"] = [author_item]
        # Series Info
        artifact_item["uri"] = response.url
        if title_obj:
            artifact_item["title"] = title_obj
        if year_obj:
            artifact_item["date_published"] = year_obj + '-01-01'
        if isbn_obj:
            if re.match(r'\d{4}-\d{4}', isbn_obj):
                artifact_item['issn'] = isbn_obj
            else:
                artifact_item['isbn_online'] = isbn_obj.replace('-', '')
        if subjects:
            artifact_item["topics"] = subjects
        if summary_obj:
            artifact_item["summary"] = summary_obj
        if city_obj:
            artifact_item["publication_place"] = city_obj

        # File Item
        if pdf_obj:
            file_item["url"] = pdf_obj
            file_item["media_type"] = "application/pdf"
            if language_obj:
                file_item["language"] = str(language_obj)
            artifact_item["files"] = [file_item]

        props = []
        prop_item = ii.PropItem()
        prop_item['key'] = "Pages"
        if pages_obj:
            prop_item['value'] = int(pages_obj)
            props.append(prop_item)
        prop_item = ii.PropItem()
        prop_item['key'] = "Classification (DDC)"
        if ddc_obj:
            prop_item['value'] = ddc_obj
            props.append(prop_item)
        prop_item = ii.PropItem()
        prop_item['key'] = "Classification (IAP)"
        if iap_obj:
            prop_item['value'] = iap_obj
            props.append(prop_item)
        if (len(prop_item) > 0):
            artifact_item['props'] = props

        ingestion_item["collection"] = collection_item
        ingestion_item["harvest"] = harvest_item
        ingestion_item["artifacts"] = [artifact_item]

        if 'uri' in artifact_item and 'title' in artifact_item:
            return ingestion_item
        else:
            self.logger.warning(f'{response.url} did not parse to a usable artifact')
            return None