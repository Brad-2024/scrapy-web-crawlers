import pycountry
import scrapy
import re
import pandas as pd
from datetime import datetime


class UnwspiderSpider(scrapy.Spider):
    name = "UNWSpider"
    allowed_domains = ["www.unwomen.org"]
    start_urls = ["https://www.unwomen.org/en/resources"]
    base_url = "https://www.unwomen.org"
    base_page_url = 'https://www.unwomen.org/en/publications'

    data = []
    flagged = []
    language_errors = []

    schema_file_path = 'schema.csv'
    schema_df = pd.read_csv(schema_file_path)
    schema_columns = schema_df.columns.tolist()

    def parse(self, response):
        for link in response.css('section.view-publications div.views-field.views-field-nothing span.field-content').getall():
            link_selector = scrapy.Selector(text=link)
            href = link_selector.css('div.search-item-title a::attr(href)').get()
            date = ''
            if link_selector.css('div.search-item-date time::text').get():
                date = link_selector.css('div.search-item-date time::text').get()
            yield scrapy.Request(url=self.base_url + href, callback=self.parse_item, meta={'date': date})
        next_page = response.css('li.pager__item.pager__item--next a::attr(href)').get()
        if next_page:
            yield scrapy.Request(url=self.base_page_url + next_page, callback=self.parse)

    def parse_item(self, response):
        if response.css('div.field__item  div.paragraph.paragraph--type--download-in.paragraph--view-mode--default').getall() != []:
            for document in response.css('div.field__item  div.paragraph.paragraph--type--download-in.paragraph--view-mode--default').getall():

                item = {col: '' for col in self.schema_columns}

                item['artifact__uri'] = response.url

                item['collection__uuid'] = '59fa1358-402b-46be-874b-2d2686f41c22'

                # title
                title = ''
                if response.css('div.left-content h1::text').get():
                    title = response.css('div.left-content h1::text').get()
                if title != '':
                    item['artifact__title'] = title.strip()
                else:
                    self.flagged.append(response.url + ' has no title')

                # date
                date_string = response.meta.get('date')
                if date_string != '':
                    date_object = datetime.strptime(date_string, "%B %d, %Y")
                    formatted_date = date_object.strftime("%Y-%m-%d")
                    item['artifact__date_published_year'] = formatted_date
                else:
                    self.flagged.append(response.url + ' has no publishing date')

                # summary
                summary = ''
                if response.xpath('//*[@id="block-hq-content"]/div/div[2]/div[2]/div/div[1]//text()').getall():
                    summary = ''.join(response.xpath('//*[@id="block-hq-content"]/div/div[2]/div[2]/div/div[1]//text()').getall())
                if summary != '':
                    item['artifact__summary'] = summary.strip()
                else:
                    self.flagged.append(response.url + ' has no summary')

                # file and language
                document_selector = scrapy.Selector(text=document)
                if document_selector.css('a::text').get():
                    try:
                        language = pycountry.languages.lookup(document_selector.css('a::text').get().strip()).alpha_2
                    except Exception:
                        language = 'unknown'
                        self.language_errors.append(document_selector.css('a::text').get() + '|||' + response.url)
                else:
                    language = None
                if document_selector.css('a::attr(href)').get():
                    pdf_link = self.base_url + document_selector.css('a::attr(href)').get()
                else:
                    pdf_link = None
                item['file__language'] = language if language else self.flagged.append(
                    response.url + ' has no language')
                item['file__url'] = pdf_link if pdf_link else self.flagged.append(response.url + ' has no pdf link')

                # publisher
                publisher = ''
                if response.css('div.field-publishing-entity a::text').get():
                    publisher = response.css('div.field-publishing-entity a::text').get().strip()
                if publisher != '':
                    item['artifact__publisher'] = publisher
                else:
                    self.flagged.append(response.url + ' has no publisher')

                # tags
                tags = ''
                if response.css('div.mb-2 a.content-tag::text').getall() != []:
                    tags = '|'.join(response.css('div.mb-2 a.content-tag::text').getall())
                if tags != '':
                    item['artifact__tags'] = tags

                item['artifact__type'] = 'report'

                # submit data
                self.data.append(item)

        elif response.css('div.tag-entities div.field ul a').getall() != []:
            for document in response.css('div.tag-entities div.field ul a').getall():

                item = {col: '' for col in self.schema_columns}

                item['artifact__uri'] = response.url

                item['collection__uuid'] = '59fa1358-402b-46be-874b-2d2686f41c22'

                # title
                title = ''
                if response.css('div.left-content h1::text').get():
                    title = response.css('div.left-content h1::text').get()
                if title != '':
                    item['artifact__title'] = title.strip()
                else:
                    self.flagged.append(response.url + ' has no title')

                # date
                date_string = response.meta.get('date')
                if date_string != '':
                    date_object = datetime.strptime(date_string, "%B %d, %Y")
                    formatted_date = date_object.strftime("%Y-%m-%d")
                    item['artifact__date_published_year'] = formatted_date
                else:
                    self.flagged.append(response.url + ' has no publishing date')

                # summary
                summary = ''
                if response.xpath('//*[@id="block-hq-content"]/div/div[2]/div[2]/div/div[1]//text()').getall():
                    summary = ''.join(response.xpath('//*[@id="block-hq-content"]/div/div[2]/div[2]/div/div[1]//text()').getall())
                if summary != '':
                    item['artifact__summary'] = summary.strip()
                else:
                    self.flagged.append(response.url + ' has no summary')

                # file and language
                document_selector = scrapy.Selector(text=document)
                if document_selector.css('a::text').get():
                    try:
                        language = pycountry.languages.lookup(document_selector.css('a::text').get().strip()).alpha_2
                    except Exception:
                        language = 'unknown'
                        self.language_errors.append(document_selector.css('a::text').get() + '|||' + response.url)
                else:
                    language = None
                if document_selector.css('a::attr(href)').get():
                    pdf_link = self.base_url + document_selector.css('a::attr(href)').get()
                else:
                    pdf_link = None
                item['file__language'] = language if language else self.flagged.append(response.url + ' has no language')
                item['file__url'] = pdf_link if pdf_link else self.flagged.append(response.url + ' has no pdf link')

                # publisher
                publisher = ''
                if response.css('div.field-publishing-entity a::text').get():
                    publisher = response.css('div.field-publishing-entity a::text').get().strip()
                if publisher != '':
                    item['artifact__publisher'] = publisher
                else:
                    self.flagged.append(response.url + ' has no publisher')

                # tags
                tags = ''
                if response.css('div.mb-2 a.content-tag::text').getall() != []:
                    tags = '|'.join(response.css('div.mb-2 a.content-tag::text').getall())
                if tags != '':
                    item['artifact__tags'] = tags

                item['artifact__type'] = 'report'

                # submit data
                self.data.append(item)

        elif response.css('div.tag-entities div.field figure').getall() != []:
            for document in response.css('div.tag-entities div.field figure').getall():

                item = {col: '' for col in self.schema_columns}

                item['artifact__uri'] = response.url

                item['collection__uuid'] = '59fa1358-402b-46be-874b-2d2686f41c22'

                # title
                title = ''
                if response.css('div.left-content h1::text').get():
                    title = response.css('div.left-content h1::text').get()
                if title != '':
                    item['artifact__title'] = title.strip()
                else:
                    self.flagged.append(response.url + ' has no title')

                # date
                date_string = response.meta.get('date')
                if date_string != '':
                    date_object = datetime.strptime(date_string, "%B %d, %Y")
                    formatted_date = date_object.strftime("%Y-%m-%d")
                    item['artifact__date_published_year'] = formatted_date
                else:
                    self.flagged.append(response.url + ' has no publishing date')

                # summary
                summary = ''
                if response.xpath('//*[@id="block-hq-content"]/div/div[2]/div[2]/div/div[1]//text()').getall():
                    summary = ''.join(response.xpath('//*[@id="block-hq-content"]/div/div[2]/div[2]/div/div[1]//text()').getall())
                if summary != '':
                    item['artifact__summary'] = summary.strip()
                else:
                    self.flagged.append(response.url + ' has no summary')

                # file and language
                document_selector = scrapy.Selector(text=document)
                if document_selector.css('a::text').get():
                    try:
                        language = pycountry.languages.lookup(document_selector.css('a::text').get().strip()).alpha_2
                    except Exception:
                        language = 'unknown'
                        self.language_errors.append(document_selector.css('a::text').get() + '|||' + response.url)
                else:
                    language = None
                if document_selector.css('a::attr(href)').get():
                    pdf_link = self.base_url + document_selector.css('a::attr(href)').get()
                else:
                    pdf_link = None
                item['file__language'] = language if language else self.flagged.append(
                    response.url + ' has no language')
                item['file__url'] = pdf_link if pdf_link else self.flagged.append(response.url + ' has no pdf link')

                # publisher
                publisher = ''
                if response.css('div.field-publishing-entity a::text').get():
                    publisher = response.css('div.field-publishing-entity a::text').get().strip()
                if publisher != '':
                    item['artifact__publisher'] = publisher
                else:
                    self.flagged.append(response.url + ' has no publisher')

                # tags
                tags = ''
                if response.css('div.mb-2 a.content-tag::text').getall() != []:
                    tags = '|'.join(response.css('div.mb-2 a.content-tag::text').getall())
                if tags != '':
                    item['artifact__tags'] = tags

                item['artifact__type'] = 'report'

                # submit data
                self.data.append(item)


    def closed(self, reason):
        df = pd.DataFrame(self.data)

        df.to_csv('unw_output.csv', index=False)

        with open('unw_flagged.txt', 'w') as f:
            for url in self.flagged:
                f.write(url + '\n')

        with open('unw_language_errors.txt', 'w') as f:
            for url in self.language_errors:
                f.write(url + '\n')
