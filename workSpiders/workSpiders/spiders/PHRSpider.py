import pandas as pd
import scrapy
import re
from datetime import datetime

class PhrspiderSpider(scrapy.Spider):
    name = "PHRSpider"
    allowed_domains = ["phr.org"]

    document_type_mapping = {
        "Report": "report",
        "Case Study": "case-study",
        "Fact Sheet": "factsheet",
        "Open Letter": "correspondence",
        "Other": "other",
        "Research Brief": "brief"
    }
    flagged = []
    data = []

    schema_file_path = 'phr_schema.csv'
    schema_df = pd.read_csv(schema_file_path)
    schema_columns = schema_df.columns.tolist()

    def start_requests(self):
        urls = []
        with open('phr_url_list.txt', 'r') as f:
            lines = f.readlines()

        for line in lines:
            url, type = line.strip().split(' | ')
            yield scrapy.Request(url=url, callback=self.parse, meta={'type': type})

    def parse(self, response):
        title = ' '.join(response.css('main.site-main#main h1.entry-title::text, main.site-main#main h1.entry-title span::text, main.site-main#main h1.entry-title a::text').getall()) or ''
        # check if response.meta['type'] contains a '|' and split it
        if '|' in response.meta['type']:
            type_list = response.meta['type'].split('|')
            new_type_list = []
            for type in type_list:
                new_type_list.append(self.document_type_mapping.get(type) or '')
            type = '|'.join(new_type_list)
        else:
            type = self.document_type_mapping.get(response.meta['type']) or ''
        date = re.sub(r'(\w+) (\d+), (\d+)', lambda m: f"{m.group(3)}-{datetime.strptime(m.group(1), '%B').strftime('%m')}-{int(m.group(2)):02d}", response.css('span.posted-on::text').get() or '') if response.css('span.posted-on::text').get() else ''

        summary = " ".join(p.xpath('string(.)').get() for p in (response.xpath(
            '//h2[contains(@class, "wp-block-heading") and contains(text(), "Executive Summary")]/following-sibling::p[following-sibling::a[@name="phr_toc_1"]]') or [])).strip() if response.xpath(
            '//h2[contains(@class, "wp-block-heading") and contains(text(), "Executive Summary")]/following-sibling::p[following-sibling::a[@name="phr_toc_1"]]') else ''
        authors = '|'.join([scrapy.Selector(text=author).css('a.card--link::text').get() for author in response.css('div.card.card--person').getall()]) if response.css('div.card.card--person').getall() else ''
        uri = response.url or ''
        pdf = response.css('div.entry-content a.wp-block-button__link.wp-element-button::attr(href)').get() or response.css('div.resources--report-download-multiple a::attr(href)').get() or response.css('div.entry-content a.wp-block-button__link::attr(href)').get() or response.css('div.resources--report-download-single a.btn::attr(href)').get() or response.css('div.entry-content div.wp-block-file a.wp-block-file__button::attr(href)').get() or ''
        if pdf == '':
            p_links = response.css('div.entry-content p a::attr(href)').getall()
            pdf = p_links[-1] if p_links and p_links[-1].endswith('.pdf') else ''
        tags = "|".join(response.css('span.entry--focus span::text').getall()) if response.css('span.entry--focus span::text').getall() else ''

        item = {col: '' for col in self.schema_columns}

        item['artifact__uri'] = uri

        item['collection__uuid'] = 'b693cdac-b16e-4685-8b4c-4f5e6d1d58d8'

        item['artifact__title'] = title if title != '' else self.flagged.append(response.url + ' has no title')
        # repeat for artifact__summary	artifact__type	artifact__date_published artifact__tags	artifact__people__author file__url
        item['artifact__summary'] = summary if summary != '' else self.flagged.append(response.url + ' has no summary')
        item['artifact__type'] = type if type != '' else self.flagged.append(response.url + ' has no type')
        item['artifact__date_published'] = date if date != '' else self.flagged.append(response.url + ' has no date')
        item['artifact__tags'] = tags if tags != '' else self.flagged.append(response.url + ' has no tags')
        item['artifact__people__author'] = authors if authors != '' else self.flagged.append(response.url + ' has no authors')

        if pdf != '':
            item['file__url'] = pdf
        else:
            return

        self.data.append(item)

    def closed(self, reason):
        df = pd.DataFrame(self.data)

        df.to_csv('phr_output.csv', index=False)

        with open('phr_flagged.txt', 'w') as f:
            for url in self.flagged:
                f.write(url + '\n')