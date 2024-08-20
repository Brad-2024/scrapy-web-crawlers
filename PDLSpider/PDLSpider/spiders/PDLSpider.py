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

# Set to -1 to crawl all the pages of a collection.
MAX_PAGES = -1

# Template for a page in a result set
PAGE_VIEW_TEMPLATE = 'http://www.panjabdigilib.org/webuser/searches/mainpage.jsp?CategoryID={cat_id}&page={page_id}&rpp=20&&viewall=1'

# The result pages use a search URL to link to items; this template allows us to compute a direct URL for an item.
ITEM_VIEW_TEMPLATE = 'http://www.panjabdigilib.org/webuser/searches/displayPage.jsp?ID={item_id}&CategoryID={cat_id}'


class PDLSpider(scrapy.Spider):
    name = 'PDLSpider'

    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1
    }

    def start_requests(self):
        with open('pdl_collections.json') as file:
            data = json.load(file)

        for collection in data:
            yield scrapy.Request(
                url=collection['url'],
                callback=self.parse_collection,
                meta=collection
            )

    def parse_collection(self, response):
        """
        Parse a collection one result page at a time
        """

        collection = response.meta

        # Parse the CategoryID out of the collection home page.
        link_re = r'.*CategoryID=(\d+).*'
        category_id = None
        match = re.search(link_re, response.url)
        if match:
            category_id = match.group(1)
        if category_id:
            collection['category_id'] = category_id
        else:
            self.logger.warn(f'Unable to parse CategoryID from {response.url}')
            yield None

        # First we yield the result page returned by the seed URL.
        yield from self.parse_result_page(response)

        # Next we fetch all the other pages in the list of pages from 2 and up
        num_of_pages = int(response.xpath('//select[@id="vgotopage"]/option/text()').getall()[-1])

        for page in range(2, num_of_pages + 1):
            if MAX_PAGES > 0 and page > MAX_PAGES:
                self.logger.warn(
                    f'Parsing of page {page} for collection {collection["title"]} reached max of {MAX_PAGES}. Exiting loop')
                break
            nextpage = PAGE_VIEW_TEMPLATE.replace('{page_id}', str(page)).replace('{cat_id}', category_id)
            yield response.follow(nextpage, self.parse_result_page, meta=collection)

    def parse_result_page(self, response):
        """
        Parse one page of results for a collection
        """

        self.logger.info(f'Parsing result page {response.url}')
        collection = response.meta
        category_id = collection['category_id']
        table = response.xpath("//table[@class='Displayable']")
        links = table.xpath(".//a[contains(@href, 'Initial')]/@href").getall()
        # Eliminate dupes
        link_set = set(links)
        for link in link_set:
            link_re = r'.*\?ID=(\d+).*'
            match = re.search(link_re, link)
            if match:
                item_id = match.group(1)
                item_link = ITEM_VIEW_TEMPLATE.replace('{item_id}', item_id).replace('{cat_id}', category_id)
                yield response.follow(item_link, self.parse_item, meta=collection)
            else:
                self.logger.warn(f'Unable to parse item ID from {link}')

    def parse_item(self, response):
        """
        Parse one item from a result page
        """

        self.logger.info(f'Parsing item at {response.url}')
        collection = response.meta
        organization_obj = collection['organization']
        series_title_obj = collection['title']
        uuid_obj = collection['uuid']
        type_obj = collection['type']

        ingestion_item = ii.IngestionItem()
        collection_item = ii.CollectionItem()
        harvest_item = ii.HarvestItem()
        file_item = ii.FileItem()
        author_item = ii.AuthorItem()
        prop_item = ii.PropItem()
        artifact_item = ii.ArtifactItem()
        thumbnail_item = ii.ThumbnailItem()

        props = []
        author_items = []

        language_codes = {
            'Bengali': 'bn',
            'Braj': 'bra',
            'English': 'en',
            'French': 'fr',
            'Hindi': 'hi',
            'Marathi': 'mr',
            'Panjabi': 'pa',
            'Persian': 'fa',
            'Prakrit': 'pra',
            'Sadh Bhasha': 'bn',
            'Sanskrit': 'sa',
            'Urdu': 'ur'
        }

        month_codes = {
            'January': '01',
            'February': '02',
            'March': '03',
            'April': '04',
            'May': '05',
            'June': '06',
            'July': '07',
            'August': '08',
            'September': '09',
            'October': '10',
            'November': '11',
            'December': '12'
        }

        keywords = response.xpath(
            "//font[@class='ubhypers'][text() = 'Keywords']/../following-sibling::td[1]//text()").getall()
        if keywords != None:
            for items in keywords:
                if '\r\n' in items:
                    keywords.remove(items)
                elif items == ', ':
                    keywords.remove(items)
                elif '[' in items:
                    keywords.remove(items)
                elif ']' in items:
                    keywords.remove(items)
                elif 'edit' in items:
                    keywords.remove(items)
                elif items == "edit":
                    keywords.remove(items)

            for items in keywords:
                if items[0] == ' ':
                    items.replace(' ', '', 1)

            for items in keywords:
                if "Click here to suggest keywords" in items:
                    keywords = None

        description = response.xpath(
            "//font[@class='ubhypers'][text() = 'Description']/../following-sibling::td[1]/text()").getall()
        description_obj = " ".join(description).strip()
        description_obj = description_obj.replace("[ ]", "")
        publisher = response.xpath(
            "//font[@class='ubhypers'][text() = 'Publisher']/../following-sibling::td[1]//text()").getall()
        publisher_obj = ''
        if publisher != []:
            publisher_obj = publisher[1]
        author = response.xpath(
            "//font[@class='ubhypers'][text() = 'Author']/../following-sibling::td[1]//text()").getall()
        author_obj = ''
        if author != []:
            author_obj = author[1]
            author_item = ii.AuthorItem()
            author_item["name"] = author_obj
            author_item["role"] = 'Author'
            author_items.append(author_item)
        editor = response.xpath(
            "//font[@class='ubhypers'][text() = 'Editor']/../following-sibling::td[1]//text()").getall()
        editor_obj = ''
        if editor != []:
            editor_obj = editor[1]
            author_item = ii.AuthorItem()
            author_item["name"] = editor_obj
            author_item["role"] = 'Editor'
            author_items.append(author_item)
        translator = response.xpath(
            "//font[@class='ubhypers'][text() = 'Translator']/../following-sibling::td[1]//text()").getall()
        translator_obj = ''
        if translator != []:
            translator_obj = translator[1]
            author_item = ii.AuthorItem()
            author_item["name"] = translator_obj
            author_item["role"] = 'Translator'
            author_items.append(author_item)
        title = response.css('a.leftList img::attr(title)').get()
        title_obj = ''
        if title != None:
            title_obj = title.replace(" online on Panjab Digital Library", '')
        year = response.xpath("//font[@class='ubhypers'][text() = 'Year']/../following-sibling::td[1]//text()").getall()
        year_obj = ''
        if year != []:
            year_obj = year[1]
        month = response.xpath(
            "//font[@class='ubhypers'][text() = 'Month']/../following-sibling::td[1]//text()").getall()
        month_obj = ''
        if month != []:
            month_obj = month[1]
        day = response.xpath("//font[@class='ubhypers'][text() = 'Day']/../following-sibling::td[1]//text()").getall()
        day_obj = ''
        if day != []:
            day_obj = day[1]
        language = response.xpath(
            "//font[@class='ubhypers'][text() = 'Language']/../following-sibling::td[1]//text()").getall()
        language_obj = ''
        if language != []:
            if ", " in language[1]:
                language_obj = language[1].split(", ")
            else:
                language_obj = [language[1]]
        pages = response.xpath(
            "//font[@class='ubhypers'][text() = 'Pages']/../following-sibling::td[1]//text()").getall()
        pages_obj = ''
        if pages != []:
            pages_obj = pages[1]
        isbn = response.xpath("//font[@class='ubhypers'][text() = 'ISBN']/../following-sibling::td[1]//text()").getall()
        isbn_obj = ''
        if isbn != []:
            isbn_obj = isbn[1]
        if isbn_obj == "NM":
            isbn_obj = ''
        completion = response.xpath(
            "//font[@class='ubhypers'][text() = 'Completion']/../following-sibling::td[1]//text()").getall()
        completion_obj = ''
        if completion != []:
            completion_obj = completion[1]
        condition = response.xpath(
            "//font[@class='ubhypers'][text() = 'Condition']/../following-sibling::td[1]//text()").getall()
        condition_obj = ''
        if condition != []:
            condition_obj = condition[1]
        custodian = response.xpath(
            "//font[@class='ubhypers'][text() = 'Custodian']/../following-sibling::td[1]//text()").getall()
        custodian_obj = ''
        if custodian != []:
            custodian_obj = custodian[1]
        issue = response.xpath(
            "//font[@class='ubhypers'][text() = 'Issue']/../following-sibling::td[1]//text()").getall()
        issue_obj = ''
        if issue != []:
            issue_obj = issue[1]
        volume = response.xpath(
            "//font[@class='ubhypers'][text() = 'Volume']/../following-sibling::td[1]//text()").getall()
        volume_obj = ''
        if volume != []:
            volume_obj = volume[1]
        script = response.xpath(
            "//font[@class='ubhypers'][text() = 'Script']/../following-sibling::td[1]//text()").getall()
        script_obj = ''
        if script != []:
            script_obj = script[1]
        accession_number_block = response.xpath(
            "//font[@class='ubhypers'][text() = 'Accession Number']/..//text()").getall()
        accession_number = ''
        if len(accession_number_block) > 0:
            accession_number = accession_number_block[1].strip()
        pdf_part = response.css('a[href*=downloadPdf]::attr(href)').get()
        pdf_obj = []
        if pdf_part != None:
            pdf_obj.append(urllib.parse.urljoin('http://www.panjabdigilib.org/webuser/searches/', pdf_part))
            pdf_items = []
            for pdfs in pdf_obj:
                file_item = ii.FileItem()
                file_item["url"] = pdfs
                file_item["media_type"] = "application/pdf"
                language_list = []
                if (language_obj != ''):
                    for item in language_obj:
                        language_list.append(language_codes[item])
                    file_item['languages'] = language_list
                pdf_items.append(file_item)
                if (len(pdf_items) > 0):
                    artifact_item["files"] = pdf_items
        else:
            pdf_obj.append(urllib.parse.urljoin('http://www.panjabdigilib.org/webuser/searches/',
                                                response.css('a[href*="displayPageContent.jsp"]::attr(href)').get()))
            pdf_items = []
            for pdfs in pdf_obj:
                file_item = ii.FileItem()
                file_item["url"] = pdfs
                file_item["media_type"] = "text/html"
                language_list = []
                if (language_obj != ''):
                    for item in language_obj:
                        language_list.append(language_codes[item])
                    file_item['languages'] = language_list
                pdf_items.append(file_item)
                if (len(pdf_items) > 0):
                    artifact_item["files"] = pdf_items
        thumbnail_link = response.css('a.leftList ::attr(src)').get()
        thumbnail_obj = ''
        if thumbnail_link != None:
            thumbnail_obj = urllib.parse.urljoin('http://www.panjabdigilib.org/',
                                                 thumbnail_link.replace('../', '').replace(" ", ""))
        url_obj = response.url

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
        # Thumbnail
        if thumbnail_obj != '':
            thumbnail_item["url"] = thumbnail_obj
            artifact_item['thumbnail'] = thumbnail_item
        # Series info
        if accession_number != '':
            artifact_item["identifier"] = accession_number
        artifact_item["uri"] = url_obj
        if title_obj != '':
            artifact_item["title"] = title_obj
        new_date = []
        if year_obj != '' and month_obj != '' and day_obj != '':
            new_date.append(year_obj)
            new_date.append(month_codes[month_obj])
            if len(day_obj) < 2:
                new_date.append(f'0{day_obj}')
            else:
                new_date.append(day_obj)
        elif year_obj != '':
            new_date.append(year_obj)
            new_date.append('01')
            new_date.append('01')
        if new_date != []:
            date_published = '-'.join(new_date)
            artifact_item['date_published'] = date_published
        if isbn_obj != '':
            artifact_item['isbn'] = isbn_obj
        # Summary
        if description_obj != '':
            artifact_item['summary'] = description_obj

        prop_item = ii.PropItem()
        prop_item['key'] = "Pages"
        if pages_obj != '':
            prop_item['value'] = int(pages_obj)
            props.append(prop_item)

        prop_item = ii.PropItem()
        prop_item['key'] = "Completion"
        if completion_obj != '':
            prop_item['value'] = completion_obj
            props.append(prop_item)

        prop_item = ii.PropItem()
        prop_item['key'] = "Condition"
        if condition_obj != '':
            prop_item['value'] = condition_obj
            props.append(prop_item)

        prop_item = ii.PropItem()
        prop_item['key'] = "Custodian"
        if custodian_obj != '':
            prop_item['value'] = custodian_obj
            props.append(prop_item)

        prop_item = ii.PropItem()
        prop_item['key'] = "Script"
        if custodian_obj != '':
            prop_item['value'] = script_obj
            props.append(prop_item)

        if (len(prop_item) > 0):
            artifact_item['props'] = props

        # Subjects
        topic_items = []
        if keywords != None:
            for items in keywords:
                if items == 'edit':
                    continue
                topic_items.append(items.strip())
            if (len(topic_items) > 0):
                artifact_item["topics"] = topic_items

        if (len(author_items) > 0):
            artifact_item["authors"] = author_items

        ingestion_item["collection"] = collection_item
        ingestion_item["harvest"] = harvest_item
        ingestion_item["artifacts"] = [artifact_item]

        if 'uri' in artifact_item and 'title' in artifact_item:
            return ingestion_item
        else:
            self.logger.warning(f'{response.url} did not parse to a usable artifact')
            return None