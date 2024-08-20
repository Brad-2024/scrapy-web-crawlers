import scrapy
from datetime import datetime
import pandas as pd
import re


class IesspiderSpider(scrapy.Spider):
    name = "IESSpider"
    allowed_domains = ["ies.ed.gov"]
    start_urls = ["https://ies.ed.gov/pubsearch/index.asp?PubSectionID=1&HasSearched=1&pubspagenum=1&sort=3&order=0&L1=&L2=&searchstring=&pagesize=100&searchtype=AND&searchcat2=&searchcat=title&searchmonth=5&searchyear=2024&datetype=le&pubtype=&centername=&center="]
    base_url = "https://ies.ed.gov/pubsearch/"
    data = []
    flagged = []

    # Load the schema file
    schema_file_path = 'Commons_CSV_schema-v2024.1.csv'
    schema_df = pd.read_csv(schema_file_path)
    schema_columns = schema_df.columns.tolist()

    def start_requests(self):
        for urls in self.start_urls:
            yield scrapy.Request(url=urls, callback=self.parse)

    def parse(self, response):
        url_list = response.css('a[href^="pubsinfo.asp?pubid="]::attr(href)').getall()
        for urls in url_list:
            yield scrapy.Request(url=self.base_url + urls, callback=self.parse_items)
        next_page = response.css('a[href*="index.asp?PubSectionID=1"][href*="pubspagenum="]:contains("Next")::attr(href)').get()
        if next_page:
            yield scrapy.Request(url=self.base_url + next_page, callback=self.parse)

    def parse_items(self, response):

        type_mapping = {
            "Applied Research Methods": "report",
            "Brochure": "brochure",
            "Compendium": "report",
            "Data File": "dataset",
            "Data Point": "report",
            "Descriptive Study": "report",
            "Directory": "directory",
            "Evaluation Brief": "brief",
            "Evaluation Report": "report",
            "Financial Tables Report": "report",
            "First Look / ED TAB": "report",
            "Guide": "guide",
            "Handbook": "guide",
            "How-To Guide": "toolkit-how-to",
            "Impact Study": "report",
            "Intervention Report": "report",
            "Issue Brief": "brief",
            "Issues and Answers Report": "report",
            "Making an Impact": "report",
            "Making Connections": "report",
            "Practice Guide": "guide",
            "Proceedings/Conference Report": "proceedings",
            "Quarterly": "report",
            "Quick Review": "report",
            "Reference Guide": "guide",
            "Research and Development Report": "report",
            "Research Report": "report",
            "Rigorous Study": "report",
            "Self-Study Guide": "guide",
            "Single Study Review": "report",
            "Snapshot": "report",
            "Stated Briefly": "brief",
            "Statistical Analysis Report": "statistical-publication",
            "Statistics in Brief": "statistical-publication",
            "Systematic Literature Review": "report",
            "Tables": "table-chart-graph",
            "Technical Brief": "brief",
            "Technical Methods Report": "report",
            "Technical/Methodological Report": "report",
            "Toolkit": "toolkit-how-to",
            "Tools": "toolkit-how-to",
            "Topic Report": "report",
            "What's Happening": "report",
            "What's Known": "report",
            "Working Paper": "discussion-paper-working-paper"
        }

        # initialize dictionary for data
        item = {col: '' for col in self.schema_columns}
        if response.css('span.TextSectionTitle::text').get() == 'There are no products with this pub number!':
            return
        # get title
        if response.css('td.TextSectionTitle::text').get():
            title = response.css('td.TextSectionTitle::text').get().strip()
        # get summary
        description = ''
        if response.css('td[itemprop="description"]::text').get():
            if response.css('td[itemprop="description"]::text').get().strip() != '':
                description = response.css('td[itemprop="description"]::text').get().strip()
            elif response.css('td[itemprop="description"] p::text').get():
                if response.css('td[itemprop="description"] p::text').get().strip() != '':
                    description = response.css('td[itemprop="description"] p::text').get().strip()
        elif response.css('td[itemprop="description"] p::text').get():
            if response.css('td[itemprop="description"] p::text').get().strip() != '':
                description = response.css('td[itemprop="description"] p::text').get().strip()
        # get opject url
        pdf_url = ''
        if response.css('td.LinkList ul li a::attr(href)').get():
            pdf_url = response.css('td.LinkList ul li a::attr(href)').get()
        # get date
        formatted_date = ''
        if response.css('tr:contains("Web Release:") td:nth-child(2)::text').get():
            date_str = response.css('tr:contains("Web Release:") td:nth-child(2)::text').get()
            date_obj = datetime.strptime(date_str.strip(), '%B %d, %Y')
            formatted_date = date_obj.strftime('%Y-%m-%d')
        # get product type and remove unwanted types
        product_type = ''
        if response.xpath('//td[strong[contains(text(), "Type of Product:")]]/following-sibling::td/a/text()').get():
            product_type = response.xpath('//td[strong[contains(text(), "Type of Product:")]]/following-sibling::td/a/text()').get()
            if product_type in ["CD/DVD", "Video", "User's Manual/Data File Documentation", "Audio"]:
                return
            else:
                product_type = type_mapping.get(product_type, "report")


        # get tags
        tags = ''
        if response.css('.SideList').xpath('string(.)').get():
            tags = response.css('.SideList').xpath('string(.)').get().strip().replace('• ', '').replace('\t', '').replace('\n','').replace('\r', '|')

        # get publisher
        publisher = ''
        if response.xpath('//td[strong[contains(text(), "Center/Program")]]/following-sibling::td/a/text()').get():
            publisher = response.xpath('//td[strong[contains(text(), "Center/Program")]]/following-sibling::td/a/text()').get()

        # author separation
        authors = ''
        if response.css('td[itemprop="author"]::text').get():
            and_pattern = re.compile(r'\s+(and|&)\s+')
            semicolon_pattern = re.compile(r'\s*;\s*')

            # replace "and" and "&" with a semicolon to handle them uniformly
            author_string = and_pattern.sub('; ', response.css('td[itemprop="author"]::text').get())

            # split by semicolon to separate potential authors
            parts = semicolon_pattern.split(author_string)

            authors = []
            buffer = []

            for part in parts:
                # handle each part
                sub_parts = part.split(',')
                for i, sub_part in enumerate(sub_parts):
                    sub_part = sub_part.strip()
                    if buffer and (sub_part.endswith('.') or re.match(r'^[A-Z]\.$', sub_part)):
                        buffer.append(sub_part)
                        authors.append(', '.join(buffer).strip())
                        buffer = []
                    else:
                        if i > 0 and buffer:
                            authors.append(', '.join(buffer).strip())
                            buffer = [sub_part]
                        else:
                            buffer.append(sub_part)

                if buffer:
                    authors.append(', '.join(buffer).strip())
                    buffer = []

            # remove any empty strings from the final list
            authors = [author for author in authors if author]

        if authors != '':
            item['artifact__people__author'] = '|'.join(authors)
        else:
            self.flagged.append(response.url + ' has no authors')

        item['artifact__uri'] = response.url

        item['collection__uuid'] = '8e194549-80b0-4441-80e3-15223ef02992'

        item['artifact__title'] = title.strip()

        if description != '':
            item['artifact__summary'] = description
        else:
            self.flagged.append(response.url + ' has no summary')

        if pdf_url != '':
            item['file__url'] = pdf_url
        else:
            self.flagged.append(response.url + ' has no pdf link')

        if formatted_date != '':
            item['artifact__date_published'] = formatted_date
        else:
            self.flagged.append(response.url + ' has no publishing date')

        if tags != '':
            item['artifact__tags'] = tags
        else:
            self.flagged.append(response.url + ' has no tags')

        if publisher != '':
            item['artifact__publisher'] = publisher
        else:
            self.flagged.append(response.url + ' has no publisher')

        if product_type != '':
            item['artifact__type'] = product_type
        else:
            self.flagged.append(response.url + ' has no product type')


        self.data.append(item)

    def closed(self, reason):
        df = pd.DataFrame(self.data)

        df.to_csv('output.csv', index=False)

        with open('flagged.txt', 'w') as f:
            for url in self.flagged:
                f.write(url + '\n')
