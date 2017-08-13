# -*- coding: utf-8 -*-

import scrapy

from pinscrapy.items import PinscrapyItem
from bs4 import BeautifulSoup
import datetime, re, json

# Based on pinboogle spider (https://github.com/spare-time/pinboogle)
class PinSpider(scrapy.Spider):
    name = 'pinboard'

    # Before: datetime after 1970-01-01 in seconds
    def __init__(self, user='notiv', before='3000000000', *args, **kwargs):
        super(PinSpider, self).__init__(*args, **kwargs)
        self.start_urls = ['https://pinboard.in/u:%s/before:%s' % (user, before)]
        self.logger.info("[PINSPIDER] Start URL: %s" % self.start_urls[0])

        self.count_users = 0
        self.user_limit = 3
        self.users_parsed = {}
        self.url_slugs_parsed = {}

    def parse(self, response):
        # fetches json representation of bookmarks instead of using css or xpath
        bookmarks = re.findall('bmarks\[\d+\] = (\{.*?\});', response.body.decode('utf-8'), re.DOTALL | re.MULTILINE)
        self.logger.info("[PINSPIDER] Bookmarks on this page: %d" % len(bookmarks))

        for bookmark in bookmarks:
            yield self.parse_bookmark(json.loads(bookmark))

        previous_page = response.css('a#top_earlier::attr(href)').extract_first()
        if previous_page:
            previous_page = response.urljoin(previous_page)
            self.logger.info("[PINSPIDER] Fetching previous page: %s" % previous_page)
            yield scrapy.Request(previous_page, callback=self.parse)

    def parse_bookmark(self, bookmark):
        if bookmark['url_slug'] in self.url_slugs_parsed:
            self.logger.info("[PINSPIDER URL has already been parsed.")
            return

        pin = PinscrapyItem()

        pin['id'] = bookmark['id']
        pin['url'] = bookmark['url']
        pin['url_slug'] = bookmark['url_slug']
        pin['url_count'] = bookmark['url_count']
        pin['title'] = bookmark['title']

        created_at = datetime.datetime.strptime(bookmark['created'], '%Y-%m-%d %H:%M:%S')
        pin['created_at'] = created_at.isoformat()
        pin['pin_fetch_date'] = datetime.datetime.utcnow().isoformat()

        pin['tags'] = bookmark['tags']
        pin['author'] = bookmark['author']

        self.url_slugs_parsed[pin['url_slug']] = 1
        request = scrapy.Request('https://pinboard.in/url:' + pin['url_slug'], callback=self.parse_url_slug)
        request.meta['pin'] = pin
        #self.logger.info("[PINSPIDER] : Parse Slug URL: %d" % len(pin['user_list']))
        return request

    def parse_url_slug(self, response):
        pin = response.meta['pin']

        pin['all_tags'] = []
        pin['user_list'] = []

        if response.body:
            soup = BeautifulSoup(response.body, 'html.parser')

            tagcloud = soup.find_all("div", id="tag_cloud")
            all_tags = [element.get_text() for element in tagcloud[0].find_all(class_='tag')]

            users = soup.find_all("div", class_="bookmark")
            user_list = [re.findall('/u:(.*)/t:', element.a['href'], re.DOTALL) for element in users]
            user_list_flat = sum(user_list, []) # Change from list of lists to list

            pin['all_tags'] = all_tags
            pin['user_list'] = user_list_flat

        return pin
