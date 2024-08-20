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
import fitz
from urllib.parse import urlparse, parse_qs


class PARILibrary(scrapy.Spider):
    name = "PARILibrary"
    start_urls = ["https://ruralindiaonline.org/en/library/"]



    def parse(self, response):
        for link in response.css('div.gallery-tile-row a::attr(href)').getall():
            yield response.follow(link, self.item_parse)
        next = response.xpath('//i[contains(@class, "fa-angle-right")]')
        if next.xpath('./parent::a/@href').get():
            yield response.follow(urllib.parse.urljoin("https://ruralindiaonline.org/en/library/", next.xpath('./parent::a/@href').get()), self.parse)

    def item_parse(self, response):
        descrpition_obj = response.xpath('//meta[@name="description"]/@content').get().strip().replace('\n', ' ')
        title_obj = response.css('title::text').get()
        thumbnail_obj = response.xpath('//meta[@property="og:image"]/@content').get()
        date_obj = response.xpath('//meta[@property="og:published_time"]/@content').get()
        link_obj = urllib.parse.urljoin("https://ruralindiaonline.org/", response.css('div.embed-container iframe::attr(src)').get())
        parsed_url = urlparse(link_obj)
        query_parameters = parse_qs(parsed_url.query)
        url_obj = urllib.parse.urljoin("https://ruralindiaonline.org" , query_parameters['file'][0])
        tag_list = []
        for tag in response.css('div.tags a.tag::text'):
            tag_list.append(tag.get().title())
        copyright_obj = response.xpath('//h4[text()="COPYRIGHT"]/following-sibling::div/p/text()').get()
        if copyright_obj:
            copyright_obj = response.xpath(
                '//h4[text()="COPYRIGHT"]/following-sibling::div/p/text()').get().strip().replace('\n', ' ')


        ingestion_item = ii.IngestionItem()
        collection_item = ii.CollectionItem()
        harvest_item = ii.HarvestItem()
        file_item = ii.FileItem()
        artifact_item = ii.ArtifactItem()
        thumbnail_item = ii.ThumbnailItem()

        # Harvest Item
        harvest_item["id"] = str(uuid.uuid4())
        harvest_item["date"] = datetime.now()
        # Collection Item
        collection_item["id"] = "5e267e04-d041-4f82-ae96-75ccb35270d3"
        collection_item["organization"] = "the-countermedia-trust"
        collection_item["title"] = 'People’s Archive of Rural India - Library'
        # Author
        authors = response.css('div.col-lg-3 p::text').get().strip().title().replace('\n', ' ')
        author_list = []
        if ', ' in authors:

            authors = authors.split(', ')
            for name in authors:
                author_item = ii.AuthorItem()
                author_item['name'] = name
                author_item['role'] = 'Author'
                author_list.append(author_item)
        else:
            author_item = ii.AuthorItem()
            author_item['name'] = authors
            author_item['role'] = 'Author'
            author_list.append(author_item)
        if len(author_list) > 0:
            artifact_item['authors'] = author_list
        # File Item
        file_item["url"] = url_obj
        file_item["media_type"] = "application/pdf"
        artifact_item["files"] = [file_item]
        # Series Info
        artifact_item['id'] = str(uuid.uuid4())
        artifact_item["title"] = title_obj
        artifact_item["date_published"] = date_obj
        if len(descrpition_obj.split('. ')) > 8:
            descrpition_obj = '. '.join(descrpition_obj.split('. ')[0:8]) + '...'
        artifact_item["summary"] = descrpition_obj
        artifact_item["uri"] = link_obj
        thumbnail_item["url"] = thumbnail_obj
        artifact_item["thumbnail"] = thumbnail_item
        if copyright_obj:
            artifact_item["rights"] = copyright_obj
        if len(tag_list) > 0:
            artifact_item['topics'] = tag_list

        ingestion_item["collection"] = collection_item
        ingestion_item["harvest"] = harvest_item
        ingestion_item["artifacts"] = [artifact_item]

        if artifact_item["uri"] and artifact_item["title"]:
            return ingestion_item
        else:
            self.logger.warning(f'{response.url} did not parse to a usable artifact')
            return None
