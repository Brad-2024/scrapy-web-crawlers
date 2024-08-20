import scrapy


class OECDSpider(scrapy.Spider):
    name = "OECDSpider"
    start_urls = ["https://legalinstruments.oecd.org/en/instruments?mode=normal&statusIds=1&dateType=adoption"]