import scrapy
from datetime import datetime
import pandas as pd
import re
import pycountry

class HohspiderSpider(scrapy.Spider):
    name = "HOHSpider"
    allowed_domains = ["www.humanitarianoutcomes.org"]
    start_urls = ["https://www.humanitarianoutcomes.org/publications"]
    base_url = "https://www.humanitarianoutcomes.org"
    big_list = []
    data = []
    flagged = []

    schema_file_path = 'Commons_CSV_schema-v2024.1.csv'
    schema_df = pd.read_csv(schema_file_path)
    schema_columns = schema_df.columns.tolist()

    def parse(self, response):
        url_list = response.css('a.card::attr(href)').getall()
        for urls in url_list:
            yield scrapy.Request(url=self.base_url + urls, callback=self.parse_items)
        if response.css('li.pager-next a::attr(href)').get():
            next_page = response.css('li.pager-next a::attr(href)').get()
            yield scrapy.Request(url=self.base_url + next_page, callback=self.parse)

    def parse_items(self, response):

        title = ''
        description = ''
        authors = ''
        language = ''
        pdf_url = ''
        formatted_date = ''

        if response.css('div.field.field-name-field-download.field-type-file.field-label-hidden').getall() != []:
            for pdfs in response.css('div.field.field-name-field-download.field-type-file.field-label-hidden').getall():

                item = {col: '' for col in self.schema_columns}

                title = response.css('header h1::text').get()

                description = ''
                if response.xpath('//hr/preceding-sibling::p[not(@style="text-align:center")]/text()').getall():
                    description = response.xpath('//hr/preceding-sibling::p[not(@style="text-align:center")]/text()').getall()
                    description = ''.join(description).strip()
                elif response.css('header div.content p::text').getall():
                    description = response.css('header div.content p::text').getall()
                    description = ''.join(description).strip()
                elif response.xpath('(//div[@class="field field-name-body field-type-text-with-summary field-label-hidden"])[1]/div[@class="field-items clearfix"]/div[@class="field-item even"]//text()').getall():
                    description = response.xpath('(//div[@class="field field-name-body field-type-text-with-summary field-label-hidden"])[1]/div[@class="field-items clearfix"]/div[@class="field-item even"]//text()').getall()
                    description = ''.join(description).strip()

                authors = ''
                if response.css('div.field.authors *::text').getall():
                    author_string = response.css('div.field.authors *::text').getall()
                    author_string = ''.join(author_string)
                    author_string = author_string.replace('By ', '')
                    authors = author_string.replace(', ', '|')

                pdf_url = scrapy.Selector(text=pdfs).css('a::attr(href)').get()
                language_text = scrapy.Selector(text=pdfs).css('a::text').get().strip().lower()
                language_text = language_text.replace('download', '').replace('\r', '').replace('\n', '').replace(
                    'summary in ', '').replace(' ( executive summary)', '').replace('research summary', '').replace('(','').replace(')', '').strip()
                if language_text == "pashto":
                    language_text = "pushto"
                if language_text == 'dali' or language_text == 'dari':
                    language_text = 'persian'

                if language_text == '':
                    language = 'en'
                elif 'summary brief' in language_text:
                    return
                else:
                    try:
                        language = pycountry.languages.lookup(language_text).alpha_2
                    except Exception:
                        language = "unknown"

                if response.css('span.date-display-single::text').get():
                    date_str = response.css('span.date-display-single::text').get()
                    date_obj = datetime.datetime.strptime(date_str, "%B %Y")
                    formatted_date = date_obj.strftime("%Y-%m-01")

                item['artifact__uri'] = response.url

                item['collection__uuid'] = '1fe251a4-ed86-40b0-be14-ca863ee1d841'

                item['artifact__title'] = title.strip()

                if description != '' and description != 'report' and description != 'the report':
                    item['artifact__summary'] = description
                else:
                    self.flagged.append(response.url + ' has no summary')

                if pdf_url != '':
                    item['file__url'] = pdf_url
                    item['file__language'] = language
                else:
                    self.flagged.append(response.url + ' has no pdf link')

                if formatted_date != '':
                    item['artifact__date_published'] = formatted_date
                else:
                    self.flagged.append(response.url + ' has no publishing date')

                if authors != '':
                    item['artifact__people__author'] = authors
                else:
                    self.flagged.append(response.url + ' has no authors')

                item['artifact__type'] = 'report'

                self.data.append(item)

        else:
            item = {col: '' for col in self.schema_columns}

            title = response.css('header h1::text').get()

            description = ''
            if response.css('header div.content p::text').getall():
                description = response.css('header div.content p::text').getall()
                description = ''.join(description).strip()
            elif response.css('header div.content p::text').getall():
                description = response.css('header div.content p::text').getall()
                description = ''.join(description).strip()
            elif response.xpath(
                    '(//div[@class="field field-name-body field-type-text-with-summary field-label-hidden"])[1]/div[@class="field-items clearfix"]/div[@class="field-item even"]//text()').getall():
                description = response.xpath(
                    '(//div[@class="field field-name-body field-type-text-with-summary field-label-hidden"])[1]/div[@class="field-items clearfix"]/div[@class="field-item even"]//text()').getall()
                description = ''.join(description).strip()

            if response.xpath('(//div[@class="field field-name-body field-type-text-with-summary field-label-hidden"])[1]//a/@href').get():
                pdf_url = response.xpath('(//div[@class="field field-name-body field-type-text-with-summary field-label-hidden"])[1]//a/@href').get()
                language = 'en'

            authors = ''
            if response.css('div.field.authors *::text').getall():
                author_string = response.css('div.field.authors *::text').getall()
                author_string = ''.join(author_string)
                author_string = author_string.replace('By ', '')
                authors = author_string.replace(', ', '|')

            if response.css('span.date-display-single::text').get():
                date_str = response.css('span.date-display-single::text').get()
                date_obj = datetime.datetime.strptime(date_str, "%B %Y")
                formatted_date = date_obj.strftime("%Y-%m-01")

            item['artifact__uri'] = response.url

            item['collection__uuid'] = '1fe251a4-ed86-40b0-be14-ca863ee1d841'

            item['artifact__title'] = title.strip()

            if description != '' and description != 'report' and description != 'the report':
                item['artifact__summary'] = description
            else:
                self.flagged.append(response.url + ' has no summary')

            if pdf_url != '':
                item['file__url'] = pdf_url
                item['file__language'] = language
            else:
                self.flagged.append(response.url + ' has no pdf link')

            if formatted_date != '':
                item['artifact__date_published'] = formatted_date
            else:
                self.flagged.append(response.url + ' has no publishing date')

            if authors != '':
                item['artifact__people__author'] = authors
            else:
                self.flagged.append(response.url + ' has no authors')

            item['artifact__type'] = 'report'

            self.data.append(item)

    def closed(self, reason):
        df = pd.DataFrame(self.data)

        df.to_csv('hoh_output.csv', index=False)

        with open('hoh_flagged.txt', 'w') as f:
            for url in self.flagged:
                f.write(url + '\n')