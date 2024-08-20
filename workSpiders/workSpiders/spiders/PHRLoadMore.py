import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError

class PHRLoadMore:
    def __init__(self):
        self.urls = []
        self.types = ["Report", "Case Study", "Fact Sheet", "Open Letter", "Other", "Research Brief"]

    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto("https://phr.org/our-work/resources/")

            # Load all documents
            while True:
                try:
                    load_more_button = page.locator('button.facetwp-load-more')
                    if load_more_button.is_visible():
                        load_more_button.click()
                        page.wait_for_timeout(2000)  # Wait for 2 seconds to ensure the content is loaded
                    else:
                        break
                except TimeoutError:
                    break

            # Collect URLs from each teaser
            for page_selector in page.locator('div.teaser').all():
                url = page_selector.locator('a.teaser--link').get_attribute('href')
                try:
                    teaser_meta = page_selector.locator('div.teaser--meta > span').inner_text()
                except TimeoutError:
                    teaser_meta = ''
                if url and teaser_meta in self.types:
                    self.urls.append((url, teaser_meta))
                elif ", " in teaser_meta:
                    teaser_list = teaser_meta.split(", ")
                    if any(item in self.types for item in teaser_list):
                        teaser_meta = "|".join(teaser_list)
                        self.urls.append((url, teaser_meta))

            browser.close()

        self.save_urls()

    def save_urls(self):
        with open('phr_url_list.txt', 'w') as f:
            for url, teaser_meta in self.urls:
                f.write(f"{url} | {teaser_meta}\n")

if __name__ == "__main__":
    spider = PHRLoadMore()
    spider.run()
