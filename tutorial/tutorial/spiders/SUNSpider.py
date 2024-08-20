import sys
sys.path.append("spiders/")

import urllib.parse
import scrapy
from datetime import datetime
import ingestion_item as ii
import uuid
import json
import re


class SUNSpider(scrapy.Spider):
    name = "SUNSpider"

    def start_requests(self):
        with open('Stellenbosch-Collections.json') as file:
            data = json.load(file)

        # Extract the URLs from the metadata
        for item in data:
            url = item['url']
            organization = item['organization']
            title = item['title']
            uuid = item['uuid']
            type = item['type']
            country = item['country']
            yield scrapy.Request(url=url, callback=self.parse_view, meta={'organization': organization, 'title': title, 'uuid': uuid, 'type': type, 'country': country})

        # Create scrapy.Request objects for each URL

    def parse_view(self, response):
        organization = response.meta.get('organization')
        title = response.meta.get('title')
        uuid = response.meta.get('uuid')
        type = response.meta.get('type')
        country = response.meta.get('country')
        view_more = urllib.parse.urljoin("https://digital.lib.sun.ac.za", response.css('p.recentSubmissionViewMore a::attr(href)').get())
        yield response.follow(view_more, self.parse_collection, meta={'organization': organization, 'title': title, 'uuid': uuid, 'type': type, 'country': country})

    def parse_collection(self, response):
        organization = response.meta.get('organization')
        title = response.meta.get('title')
        uuid = response.meta.get('uuid')
        type = response.meta.get('type')
        country = response.meta.get('country')
        for link in response.css('h4.artifact-title a::attr(href)').getall():
            document_link = urllib.parse.urljoin("https://digital.lib.sun.ac.za", link)
            yield response.follow(document_link, self.parse_document, meta={'organization': organization, 'title': title, 'uuid': uuid, 'type': type, 'country': country})

        next_page = response.css('a.next-page-link::attr(href)').get()
        if next_page:
            next_page = urllib.parse.urljoin("https://digital.lib.sun.ac.za", next_page)
            yield response.follow(next_page, self.parse_collection, meta={'organization': organization, 'title': title, 'uuid': uuid, 'type': type, 'country': country})

    # Grabbing Thumbnail Url and continuing to metadata page
    def parse_document(self, response):
        organization = response.meta.get('organization')
        title = response.meta.get('title')
        uuid = response.meta.get('uuid')
        type = response.meta.get('type')
        country = response.meta.get('country')
        thumbnail_obj = urllib.parse.urljoin("https://digital.lib.sun.ac.za", response.css('div.col-xs-6 img::attr(src)').get())
        meta_link = urllib.parse.urljoin("https://digital.lib.sun.ac.za", response.css('div.simple-item-view-show-full a::attr(href)').get())
        yield response.follow(meta_link, self.parse_meta, meta={'thumbnail_obj': thumbnail_obj, 'organization': organization, 'title': title, 'uuid': uuid, 'type': type, 'country': country})

    def parse_meta(self, response):
        organization_obj = response.meta.get('organization')
        series_title_obj = response.meta.get('title')
        uuid_obj = response.meta.get('uuid')
        type_obj = response.meta.get('type')
        country_obj = response.meta.get('country')
        thumbnail_obj = response.meta.get('thumbnail_obj')
        ingestion_item = ii.IngestionItem()
        collection_item = ii.CollectionItem()
        harvest_item = ii.HarvestItem()
        file_item = ii.FileItem()
        author_item = ii.AuthorItem()
        prop_item = ii.PropItem()
        artifact_item = ii.ArtifactItem()
        thumbnail_item = ii.ThumbnailItem()

        if (response.xpath('//meta[@name="DC.title"]/@content').get() != None):
            title_obj = response.xpath('//meta[@name="DC.title"]/@content').get().replace('\n', ' ').replace('\r', '')
        link_obj = response.xpath('//meta[@name="citation_abstract_html_url"]/@content').get()
        authors_obj = []
        editors_obj = []
        if response.xpath('//meta[@name="DC.contributor"]/@content').getall():
            for names in response.xpath('//meta[@name="DC.contributor"]/@content').getall():
                editors_obj.append(names)
        if response.xpath('//meta[@name="DC.creator"]/@content').getall():
            for names in response.xpath('//meta[@name="DC.creator"]/@content').getall():
                authors_obj.append(names)
        date_obj = []
        earliest_date = ''
        latest_date = ''
        if response.xpath('//meta[@name="DCTERMS.issued"]/@content').get():
            date_obj = response.xpath('//meta[@name="DCTERMS.issued"]/@content').get()
            earliest_date = date_obj
        elif response.xpath('//meta[@name="DCTERMS.created"]/@content').get():
            date_obj = response.xpath('//meta[@name="DCTERMS.created"]/@content').getall()
            date_obj.sort()
            earliest_date = date_obj[0]
            if len(date_obj) > 1:
                latest_date = date_obj[-1]
        pdf_obj = response.css('div.file-link a::attr(href)').getall()
        uri_obj = response.xpath('//meta[@name="DC.identifier" and @scheme="DCTERMS.URI"]/@content').get()
        rights_obj = response.xpath('//meta[@name="DC.rights"]/@content').get()
        abstract_obj = ''
        if (response.xpath('//meta[@name="DCTERMS.abstract"]/@content').get() != None):
            abstract_obj = response.xpath('//meta[@name="DCTERMS.abstract"]/@content').get().replace('\n', ' ').replace('\r', '').replace('\"', "'")
        language_obj = response.xpath('//meta[@name="DC.language"]/@content').getall()
        subjects_obj = response.xpath('//meta[@name="DC.subject"]/@content').getall()
        page_numbers = response.css('meta[name="DCTERMS.extent"]::attr(content)').getall()
        page_obj = []
        for number in page_numbers:
            matches = re.findall(r'\d+', number)
            page_obj.extend(matches)
        publisher_obj = ''
        if (response.xpath('//meta[@name="DC.publisher"]/@content').get() != None):
            publisher_obj = response.xpath('//meta[@name="DC.publisher"]/@content').get().replace('\n', ' ').replace('\r', '').replace('\"', "'")
        else:
            publisher_obj = 'Stellenbosch University'

        # Harvest Item
        harvest_item["id"] = str(uuid.uuid4())
        harvest_item["date"] = datetime.now()
        # Collection Item
        collection_item["id"] = uuid_obj
        collection_item["title"] = series_title_obj
        collection_item["organization"] = organization_obj
        # ID and Publisher
        artifact_item['id'] = str(uuid.uuid4())
        artifact_item['type'] = type_obj
        if (len(publisher_obj) > 0):
            artifact_item['publisher'] = publisher_obj
        artifact_item['publication_place'] = country_obj
        # File Item
        pdf_items = []
        for pdfs in pdf_obj:
            file_item = ii.FileItem()
            file_item["url"] = urllib.parse.urljoin("https://digital.lib.sun.ac.za", pdfs)
            file_item["media_type"] = "application/pdf"
            if (len(language_obj) > 0):
                file_item['languages'] = language_obj
            pdf_items.append(file_item)
            if (len(pdf_items) > 0):
                artifact_item["files"] = pdf_items
        # Author
        author_items = []
        for names in authors_obj:
            author_item = ii.AuthorItem()
            author_item["name"] = names
            author_item["role"] = 'Author'
            author_items.append(author_item)
        for names in editors_obj:
            author_item = ii.AuthorItem()
            author_item["name"] = names
            author_item["role"] = 'Editor'
            author_items.append(author_item)
        if (len(author_items) > 0):
            artifact_item["authors"] = author_items
        # Rights
        artifact_item["rights"] = rights_obj
        # Thumbnail
        thumbnail_item["url"] = thumbnail_obj
        artifact_item['thumbnail'] = thumbnail_item
        # Series info
        artifact_item["identifier"] = link_obj
        artifact_item["uri"] = uri_obj
        artifact_item["title"] = title_obj
        artifact_item["series"] = series_title_obj
        if (len(date_obj) > 0):
            artifact_item['date_published'] = earliest_date
        if (latest_date):
            artifact_item['date_circa'] = f'{earliest_date} to {latest_date}'
        # Rights and Summary
        artifact_item['rights'] = rights_obj
        if (len(abstract_obj) > 0):
            artifact_item['summary'] = abstract_obj
        # Page Number
        page_items = []
        for pages in page_obj:
            prop_item = ii.PropItem()
            prop_item['key'] = "Pages"
            if (len(page_obj) > 0):
                prop_item['value'] = pages
            page_items.append(prop_item)
            if (len(prop_item) > 0):
                artifact_item['props'] = page_items
        # Subjects
        topic_items = []
        for subject in subjects_obj:
            print(subject)
            topic_items.append(subject)
        if (len(topic_items) > 0):
            artifact_item["topics"] = topic_items

        ingestion_item["collection"] = collection_item
        ingestion_item["harvest"] = harvest_item
        ingestion_item["artifacts"] = [artifact_item]

        if artifact_item["uri"] and artifact_item["title"]:
            return ingestion_item
        else:
            self.logger.warning(f'{response.url} did not parse to a usable artifact')
            return None
