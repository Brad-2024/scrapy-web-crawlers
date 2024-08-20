import pandas as pd
import scrapy


class EtaspiderSpider(scrapy.Spider):
    name = "ETASpider"
    allowed_domains = ["eta-publications.lbl.gov"]
    start_urls = ["https://eta-publications.lbl.gov/publications"]

    data = []
    flagged = []

    schema_file_path = 'eta_schema.csv'
    schema_df = pd.read_csv(schema_file_path)
    schema_columns = schema_df.columns.tolist()

    type_mapping = {
        'Database': 'dataset',
        'Report': 'report',
        'Presentation': 'presentation-lecture',
        'Journal Article': 'article',
        'Policy Brief': 'brief',
        'Conference Paper': 'conference-paper',
        'Magazine Article': 'magazine',
        'Software': 'multimedia',
        'Conference Proceedings': 'proceedings',
        'Journal': 'journal',
        'Book': 'book',
        'Web Article': 'blog',
        'Book Chapter': 'chapter',
        'Government Report': 'report',
        'Miscellaneous': 'other',
        'Unpublished': 'manuscript',
        'Case Study': 'case-study',
        'Manuscript': 'manuscript',
        'Chart': 'table-chart-graph',
        'Patent': 'legal',
        'Miscellaneous Section': 'other',
        'Thesis': 'thesis-dissertation',
        'Newspaper Article': 'newspaper',
        'Broadcast': 'audio',
        'Website': 'link',
        'Hearing': 'testimony'
    }

    base_url = 'https://eta-publications.lbl.gov'

    def parse(self, response):
        for link in response.css('div.biblio-entry a::attr(href)').getall():
            if '/export/' not in link:
                if link.startswith("/publications"):
                    yield response.follow(self.base_url + link, self.parse_document)

        if response.css('li.pager-next a::attr(href)').get():
            yield response.follow(self.base_url + response.css('li.pager-next a::attr(href)').get(), self.parse)

    def parse_document(self, response):
        item = {col: '' for col in self.schema_columns}

        # File URL
        files = response.css('div.field.field-name-field-files div.field-item span.file').getall()
        pdf_links = []
        if files != []:
            for file in files:
                file_selector = scrapy.Selector(text=file)
                a_tag = file_selector.css('a')

                # Check if the <a> tag exists and if it has a href attribute
                if a_tag and a_tag.xpath('@href').get():
                    # Check if the type attribute contains 'application/pdf'
                    if 'application/pdf' in a_tag.xpath('@type').get():
                        # Get the href
                        href = a_tag.xpath('@href').get()
                        pdf_links.append(href)

            # If exactly one PDF link is found, set it to file_url
            if len(pdf_links) == 1:
                file_url = pdf_links[0]
            else:
                return
        else:
            return
        item['file__url'] = file_url

        # Title
        title = response.css('h1.title::text').get() or ''
        item['artifact__title'] = title if title else self.flagged.append(response.url + ' has no title')
        # Summary
        summary = response.css('div.biblio_field span::text').get() or ''
        item['artifact__summary'] = summary if summary else self.flagged.append(response.url + ' has no summary')
        # Authors
        authors = '|'.join(response.css('div.biblio_field.biblio_authors_data.biblio_authors a::text').getall()) if response.css('div.biblio_field.biblio_authors_data.biblio_authors a::text').getall() else ''
        item['artifact__people_author'] = authors if authors else self.flagged.append(response.url + ' has no authors')
        # Publication Year
        publication_year = response.css('div.biblio_field.biblio_year_data.biblio_year::text').get() or ''
        item['artifact__date_published_year'] = publication_year if publication_year else self.flagged.append(response.url + ' has no publication year')
        # DOI
        doi = response.css('div.biblio_field.biblio_doi_data.biblio_doi a::attr(href)').get() or ''
        item['atrifact__doi'] = doi if doi else self.flagged.append(response.url + ' has no DOI')
        # Type
        type = self.type_mapping.get(response.css('div.biblio_field.publication_type_data.publication_type::text').get(), '') if response.css('div.biblio_field.publication_type_data.publication_type::text').get() else ''
        item['artifact__type'] = type if type else self.flagged.append(response.url + ' has no type')

        # URI
        item['artifact__uri'] = response.url

        # Collection UUID
        item['collection__uuid'] = '8f691629-ae5d-4ba0-9250-6062a938a0ca'

        # Submit Data
        self.data.append(item)

    def closed(self, reason):
        df = pd.DataFrame(self.data)

        df.to_csv('eta_output.csv', index=False)

        with open('eta_flagged.txt', 'w') as f:
            for url in self.flagged:
                f.write(url + '\n')
