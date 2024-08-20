import scrapy
import datetime
import pandas as pd
import re
import pycountry

class BslspiderSpider(scrapy.Spider):
    name = "BSLSpider"
    allowed_domains = ["www.bsl.org.au"]
    start_urls = ["https://www.bsl.org.au/research/publications/"]

    data = []
    flagged = []
    other_types = []

    schema_file_path = 'schema.csv'
    schema_df = pd.read_csv(schema_file_path)
    schema_columns = schema_df.columns.tolist()

    def parse(self, response):
        for link in response.css('li.bsl-card-list__item').getall():
            list_item = link
            list_item_selector = scrapy.Selector(text=list_item)
            subtitle_text = list_item_selector.css('small.bsl-card__subtitle::text').get().strip().title()
            href = list_item_selector.css('a.bsl-card__overlay-link::attr(href)').get()
            if href == None:
                if list_item_selector.css('a.bsl-card__overlay-link::attr(data-gtm-href)').get():
                    href = 'https://www.bsl.org.au' + list_item_selector.css('a.bsl-card__overlay-link::attr(data-gtm-href)').get()
            if href == None:
                self.flagged.append(list_item_selector.css('h3.bsl-card__title a::text').get().strip() + ' on ' + response.url + ' href not there')
            if subtitle_text == 'Policy Submission':
                formatted_date = ''

                item = {col: '' for col in self.schema_columns}

                if list_item_selector.css('h3.bsl-card__title a::text').get():
                    title = list_item_selector.css('h3.bsl-card__title a::text').get().strip()
                if list_item_selector.css('div.bsl-card__meta span::text').get():
                    date_str = list_item_selector.css('div.bsl-card__meta span::text').get().strip()
                    date_obj = datetime.datetime.strptime(date_str, "%B %Y")
                    formatted_date = date_obj.strftime("%Y-%m-01")
                document_type = 'report'

                item['artifact__uri'] = href
                self.flagged.append(title + ' on ' + response.url + ' has no summary')
                self.flagged.append(title + ' on ' + response.url + ' has no authors')

                item['collection__uuid'] = '2dcb7b8e-71ad-4c9a-b018-994cda9ed0cb'

                item['artifact__title'] = title

                if formatted_date != '':
                    item['artifact__date_published'] = formatted_date
                else:
                    self.flagged.append(title + ' on ' + response.url + ' has no publishing date')

                item['artifact__type'] = document_type

                item['file__url'] = href

                self.data.append(item)

            elif subtitle_text == 'Presentation':
                formatted_date = ''

                item = {col: '' for col in self.schema_columns}

                if list_item_selector.css('h3.bsl-card__title a::text').get():
                    title = list_item_selector.css('h3.bsl-card__title a::text').get().strip()
                if list_item_selector.css('div.bsl-card__meta span::text').get():
                    date_str = list_item_selector.css('div.bsl-card__meta span::text').get().strip()
                    date_obj = datetime.datetime.strptime(date_str, "%B %Y")
                    formatted_date = date_obj.strftime("%Y-%m-01")
                document_type = 'presentation'

                item['artifact__uri'] = href
                self.flagged.append(title + ' on ' + response.url + ' has no summary')
                self.flagged.append(title + ' on ' + response.url + ' has no authors')

                item['collection__uuid'] = '2dcb7b8e-71ad-4c9a-b018-994cda9ed0cb'

                item['artifact__title'] = title

                if formatted_date != '':
                    item['artifact__date_published'] = formatted_date
                else:
                    self.flagged.append(title + ' on ' + response.url + ' has no publishing date')

                item['artifact__type'] = document_type

                item['file__url'] = href

                self.data.append(item)

            elif subtitle_text == 'Topic Guide':
                date = ''
                authors = ''

                item = {col: '' for col in self.schema_columns}

                if list_item_selector.css('h3.bsl-card__title a::text').get():
                    title = list_item_selector.css('h3.bsl-card__title a::text').get().strip()
                if list_item_selector.css('div.bsl-card__meta span::text').get():
                    text = list_item_selector.css('div.bsl-card__meta span::text').get().strip()
                    text = text.replace('By ', '').replace(', ', '|').replace(' and ', '|')
                    date_match = re.search(r'\d{4}', text)
                    date = date_match.group(0) if date_match else ''
                    authors = re.sub(r'\d{4}', '', text).strip()
                document_type = 'report'

                item['artifact__uri'] = href
                self.flagged.append(title + ' on ' + response.url + ' has no summary')

                item['collection__uuid'] = '2dcb7b8e-71ad-4c9a-b018-994cda9ed0cb'

                item['artifact__title'] = title

                if date != '':
                    item['artifact__date_published_year'] = date
                else:
                    self.flagged.append(title + ' on ' + response.url + ' has no publishing date')

                if authors != '':
                    item['artifact__people__author'] = authors
                else:
                    self.flagged.append(title + ' on ' + response.url + ' has no authors')

                item['artifact__type'] = document_type

                item['file__url'] = href

                self.data.append(item)

            elif subtitle_text == 'Research Report':
                yield scrapy.Request(url='https://www.bsl.org.au' + href, callback=self.parse_research_report)
            elif subtitle_text == 'Working Paper':
                yield scrapy.Request(url='https://www.bsl.org.au' + href, callback=self.parse_working_paper)
            else:
                self.other_types.append(subtitle_text + ' ' + response.url)
        if response.css('a.bsl-pagination__btn.bsl-btn::attr(href)').get():
            next_page = response.css('a.bsl-pagination__btn.bsl-btn::attr(href)').get()
            yield scrapy.Request(url='https://www.bsl.org.au' + next_page, callback=self.parse)

    def parse_research_report(self, response):
        title = ''
        summary = ''
        date = ''
        authors = ''
        url = ''

        item = {col: '' for col in self.schema_columns}

        if response.css('h1.bsl-masthead__title::text'):
            title = response.css('h1.bsl-masthead__title::text').get().strip()
        if response.css('p.body-m::text').get():
            summary = response.css('p.body-m::text').get().strip()
        if response.css('div.bsl-sidebar dd::text').getall()[-1]:
            date = response.css('div.bsl-sidebar dd::text').getall()[-1]
        if response.css('ul.margin-b.bsl-link-list a::attr(href)').get():
            url = response.css('ul.margin-b.bsl-link-list a::attr(href)').get()
        if response.css('div.bsl-sidebar dd::text').getall()[0]:
            authors = response.css('div.bsl-sidebar dd::text').getall()[0]
            if ' and ' in authors:
                authors = authors.replace(' and ', '|')
        document_type = "report"

        item['artifact__uri'] = response.url

        item['collection__uuid'] = '2dcb7b8e-71ad-4c9a-b018-994cda9ed0cb'

        if title != '':
            item['artifact__title'] = title
        else:
            self.flagged.append(response.url + ' has no title')

        if summary != '':
            item['artifact__summary'] = summary
        else:
            self.flagged.append(response.url + ' has no summary')

        if date != '':
            item['artifact__date_published_year'] = date
        else:
            self.flagged.append(response.url + ' has no publishing date')

        if authors != '':
            item['artifact__people__author'] = authors
        else:
            self.flagged.append(response.url + ' has no authors')

        if url != '':
            item['file__url'] = url
        else:
            self.flagged.append(response.url + ' has no pdf link')

        item['artifact__type'] = document_type

        self.data.append(item)

    def parse_working_paper(self, response):
        title = ''
        summary = ''
        date = ''
        authors = ''
        url = ''

        item = {col: '' for col in self.schema_columns}

        if response.css('h1.bsl-masthead__title::text'):
            title = response.css('h1.bsl-masthead__title::text').get().strip()
        if response.css('p.body-m::text').get():
            summary = response.css('p.body-m::text').get().strip()
        if response.css('div.bsl-sidebar dd::text').getall()[-1]:
            date = response.css('div.bsl-sidebar dd::text').getall()[-1]
        if response.css('ul.margin-b.bsl-link-list a::attr(href)').get():
            url = response.css('ul.margin-b.bsl-link-list a::attr(href)').get()
        if response.css('div.bsl-sidebar dd::text').getall()[0]:
            authors = response.css('div.bsl-sidebar dd::text').getall()[0]
            if ' and ' in authors:
                authors = authors.replace(' and ', '|')
        document_type = "report"

        item['artifact__uri'] = response.url

        item['collection__uuid'] = '2dcb7b8e-71ad-4c9a-b018-994cda9ed0cb'

        if title != '':
            item['artifact__title'] = title
        else:
            self.flagged.append(response.url + ' has no title')

        if summary != '':
            item['artifact__summary'] = summary
        else:
            self.flagged.append(response.url + ' has no summary')

        if date != '':
            item['artifact__date_published_year'] = date
        else:
            self.flagged.append(response.url + ' has no publishing date')

        if authors != '':
            item['artifact__people__author'] = authors
        else:
            self.flagged.append(response.url + ' has no authors')

        if url != '':
            item['file__url'] = url
        else:
            self.flagged.append(response.url + ' has no pdf link')

        item['artifact__type'] = document_type

        self.data.append(item)

    def closed(self, reason):
        df = pd.DataFrame(self.data)

        df.to_csv('bsl_output.csv', index=False)

        with open('bsl_flagged.txt', 'w') as f:
            for url in self.flagged:
                f.write(url + '\n')

        with open('bsl_other_types.txt', 'w') as f:
            for url in self.other_types:
                f.write(url + '\n')

