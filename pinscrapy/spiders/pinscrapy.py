# -*- coding: utf-8 -*-

import scrapy

from pinscrapy.items import PinscrapyItem
from bs4 import BeautifulSoup
import datetime, re, json


class PinSpider(scrapy.Spider):
    name = 'pinboard'

    # Before: datetime after 1970-01-01 in seconds
    def __init__(self, user='notiv', before='3000000000', *args, **kwargs):
        super(PinSpider, self).__init__(*args, **kwargs)
        self.start_urls = ['https://pinboard.in/u:%s/before:%s' % (user, before)]
        self.logger.info("[PINSPIDER] Start URL: %s" % self.start_urls[0])

    def parse(self, response):
        # fetches json representation of bookmarks instead of using css or xpath
        bookmarks = re.findall('bmarks\[\d+\] = (\{.*?\});', response.body.decode('utf-8'), re.DOTALL | re.MULTILINE)
        self.logger.info("[PINSPIDER] Bookmarks on this page: %d" % len(bookmarks))

        for bookmark in bookmarks:
            pass
            # print(bookmarks)
            yield self.parse_bookmark(json.loads(bookmark))

        previous_page = response.css('a#top_earlier::attr(href)').extract_first()
        if previous_page:
            previous_page = response.urljoin(previous_page)
            self.logger.info("[PINSPIDER] Fetching previous page: %s" % previous_page)
            yield scrapy.Request(previous_page, callback=self.parse)

    def parse_bookmark(self, bookmark):
        pin = PinscrapyItem()

        pin['id'] = bookmark['id']
        pin['url'] = bookmark['url']
        pin['url_slug'] = bookmark['url_slug']
        pin['url_count'] = bookmark['url_count']
        pin['title'] = bookmark['title']

        created_at = datetime.datetime.strptime(bookmark['created'], '%Y-%m-%d %H:%M:%S')
        pin_fetch_date = datetime.datetime.utcnow().isoformat()
        pin['created_at'] = created_at.isoformat()

        pin['tags'] = bookmark['tags']
        pin['author'] = bookmark['author']

        request = scrapy.Request(pin['url'], callback=self.parse_external_link)
        request.meta['pin'] = pin  # this passes over the pin item to the request
        return request

    def parse_external_link(self, response):
        pin = response.meta['pin']

        pin['html_fetch_date'] = datetime.datetime.utcnow().isoformat()
        pin['html_code'] = response.status
        pin['html_content'] = ""
        pin['html_content_size'] = 0
        if response.body:
            soup = BeautifulSoup(response.body, 'html.parser')
            # http://stackoverflow.com/questions/22799990/beatifulsoup4-get-text-still-has-javascript
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            pin['html_content'] = text
            pin['html_content_size'] = len(pin['html_content'])

        return pin
