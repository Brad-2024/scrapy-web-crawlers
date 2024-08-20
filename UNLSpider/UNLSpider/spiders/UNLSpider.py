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

class UNLSpider(scrapy.Spider):
    name = "UNLSpider"
    start_urls = ['https://digitalcommons.unl.edu/afghanenglish/index.html', 'https://digitalcommons.unl.edu/afghanenglish/index.2.html']

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

        edition = ''
        publication_place = ''
        publisher = ''
        publication_year = ''
        pages = ''
        if response.css('div#comments.element p::text').get() != None:
            comment_obj = response.css('div#comments.element p::text').get()
            re1 = r'(.*) : (.*), (\d\d\d\d). (.*), (\d+) p(.*)'
            match1 = re.search(re1, comment_obj)
            if match1 != None:
                publication_place = match1.group(1)
                publisher = match1.group(2)
                publication_year = match1.group(3)
                pages = match1.group(5)
            re2 = r'(.*)\. (.*): (.*), (\d\d\d\d). (\d+) p(.*)'
            match2 = re.search(re2, comment_obj)
            if match2 != None:
                edition = match2.group(1)
                publication_place = match2.group(2)
                publisher = match2.group(3)
                publication_year = match2.group(4)
                pages = match2.group(5)
            re3 = r'(.*): (.*), (\d\d\d\d).'
            match3 = re.search(re3, comment_obj)
            if match3 != None:
                publication_place = match3.group(1)
                publisher = match3.group(2)
                publication_year = match3.group(3)


        link_obj = response.meta.get('link')
        pdf_obj = response.xpath('//meta[@name="bepress_citation_pdf_url"]/@content').getall()
        summary_obj = ''
        if response.css('div#abstract.element p::text').getall() != None:
            summary_obj = response.css('div#abstract.element p::text').getall()
            new_summary = ''
            for item in summary_obj:
                new_summary += item
            summary_obj = new_summary.replace('\n', '')
        if publication_year != '':
            date_obj = [publication_year]
        else:
            date_obj = response.css('div#publication_date.element p::text').get()
        title_obj = response.css('div#title.element ::text').getall()
        new_string = ""
        for item in title_obj:
            new_string += item
        title_obj = new_string.replace('\n', '').replace('Title', '')
        if "Kabul Times" in title_obj:
            return None
        thumbnail_url = thum_io_base + urllib.parse.quote_plus(link_obj)
        thumbnail_item['url'] = thumbnail_url
        artifact_item['thumbnail'] = thumbnail_item
        # Harvest Item
        harvest_item["id"] = str(uuid.uuid4())
        harvest_item["date"] = datetime.now()
        # Collection Item
        collection_item["id"] = 'd8efb97a-88d1-4383-b8e1-4c4a92baa7e4'
        collection_item["title"] = 'Arthur Paul Afghanistan Collection'
        collection_item["organization"] = 'university-of-nebraskalincoln-us'
        # ID and Publisher
        artifact_item['id'] = str(uuid.uuid4())
        artifact_item['type'] = 'other'
        if publisher != '':
            artifact_item['publisher'] = publisher
        if publication_place != '':
            artifact_item['publication_place'] = publication_place
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
        artifact_item["series"] = "Arthur Paul Afghanistan Collection"
        if summary_obj != '':
            artifact_item["summary"] = summary_obj
        if "-" in date_obj:
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
        elif " " in date_obj:
            new_date_parts = []
            date_parts = date_obj.split(" ")
            if date_parts[0] == "January":
                new_date_parts.append(date_parts[1])
                new_date_parts.append("01")
                new_date_parts.append("01")
            if date_parts[0] == "February":
                new_date_parts.append(date_parts[1])
                new_date_parts.append("02")
                new_date_parts.append("01")
            if date_parts[0] == "March":
                new_date_parts.append(date_parts[1])
                new_date_parts.append("03")
                new_date_parts.append("01")
            if date_parts[0] == "April":
                new_date_parts.append(date_parts[1])
                new_date_parts.append("04")
                new_date_parts.append("01")
            if date_parts[0] == "May":
                new_date_parts.append(date_parts[1])
                new_date_parts.append("05")
                new_date_parts.append("01")
            if date_parts[0] == "June":
                new_date_parts.append(date_parts[1])
                new_date_parts.append("06")
                new_date_parts.append("01")
            if date_parts[0] == "July":
                new_date_parts.append(date_parts[1])
                new_date_parts.append("07")
                new_date_parts.append("01")
            if date_parts[0] == "August":
                new_date_parts.append(date_parts[1])
                new_date_parts.append("08")
                new_date_parts.append("01")
            if date_parts[0] == "September":
                new_date_parts.append(date_parts[1])
                new_date_parts.append("09")
                new_date_parts.append("01")
            if date_parts[0] == "October":
                new_date_parts.append(date_parts[1])
                new_date_parts.append("10")
                new_date_parts.append("01")
            if date_parts[0] == "November":
                new_date_parts.append(date_parts[1])
                new_date_parts.append("11")
                new_date_parts.append("01")
            if date_parts[0] == "December":
                new_date_parts.append(date_parts[1])
                new_date_parts.append("12")
                new_date_parts.append("01")
        else:
            new_date_parts = []
            new_date_parts.append(date_obj[0])
            new_date_parts.append('01')
            new_date_parts.append('01')

        date_published = '-'.join(new_date_parts)
        artifact_item['date_published'] = date_published


        prop_items = []
        if pages != '':
            page_obj = pages
            prop_item = ii.PropItem()
            prop_item['key'] = "Pages"
            if (len(page_obj) > 0):
                prop_item['value'] = page_obj
            prop_items.append(prop_item)

        if edition != '':
            edition_obj = edition
            prop_item = ii.PropItem()
            prop_item['key'] = "Edition"
            if (len(page_obj) > 0):
                prop_item['value'] = edition_obj
            prop_items.append(prop_item)
        if (len(prop_items) > 0):
            artifact_item['props'] = [prop_items]

        ingestion_item["collection"] = collection_item
        ingestion_item["harvest"] = harvest_item
        ingestion_item["artifacts"] = [artifact_item]

        if artifact_item["uri"] and artifact_item["title"]:
            return ingestion_item
        else:
            self.logger.warning(f'{response.url} did not parse to a usable artifact')
            return None