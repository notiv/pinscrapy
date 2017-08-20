# -*- coding: utf-8 -*-

import scrapy

from pinscrapy.items import PinscrapyItem, UrlSlugItem
from bs4 import BeautifulSoup
import datetime, re, json

class PinSpider(scrapy.Spider):
    name = 'pinboard'

    # Before = datetime after 1970-01-01 in seconds, used to separate the bookmark pages of a user
    def __init__(self, user='notiv', before='3000000000', *args, **kwargs):
        super(PinSpider, self).__init__(*args, **kwargs)
        self.start_urls = ['https://pinboard.in/u:%s/before:%s' % (user, before)]
        self.before = before

    def parse(self, response):
        # fetches json representation of bookmarks instead of using css or xpath
        bookmarks = re.findall('bmarks\[\d+\] = (\{.*?\});', response.body.decode('utf-8'), re.DOTALL | re.MULTILINE)

        for b in bookmarks:
            bookmark = json.loads(b)
            yield from self.parse_bookmark(bookmark)

        # Get bookmarks in previous pages
        previous_page = response.css('a#top_earlier::attr(href)').extract_first()
        if previous_page:
            previous_page = response.urljoin(previous_page)
            yield scrapy.Request(previous_page, callback=self.parse)

        return

    def parse_bookmark(self, bookmark):
        pin = PinscrapyItem()

        pin['url_slug'] = bookmark['url_slug']
        pin['title'] = bookmark['title']
        pin['author'] = bookmark['author']

        yield pin
        yield scrapy.Request('https://pinboard.in/url:' + pin['url_slug'], callback=self.parse_url_slug)

    def parse_url_slug(self, response):
        url_slug = UrlSlugItem()

        if response.body:
            soup = BeautifulSoup(response.body, 'html.parser')

            users = soup.find_all("div", class_="bookmark")
            user_list = [re.findall('/u:(.*)/t:', element.a['href'], re.DOTALL) for element in users]
            user_list_flat = sum(user_list, []) # Change from list of lists to list

            url_slug['user_list'] = user_list_flat

            yield url_slug
            for user in user_list:
                yield scrapy.Request('https://pinboard.in/u:%s/before:%s' % (user, self.before), callback=self.parse)
