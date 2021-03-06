# -*- coding: utf-8 -*-

import scrapy

from pinscrapy.items import PinItem, UrlSlugItem, PageItem
from bs4 import BeautifulSoup
import datetime, re, json

# Based on pinboogle spider (https://github.com/spare-time/pinboogle)
class PinSpider(scrapy.Spider):
    name = 'pinboard'

    # Before = datetime after 1970-01-01 in seconds, used to separate the bookmark pages of a user
    def __init__(self, user='notiv', before='3000000000', *args, **kwargs):
        super(PinSpider, self).__init__(*args, **kwargs)
        self.start_urls = ['https://pinboard.in/u:%s/before:%s' % (user, before)]
        self.start_user = user
        self.logger.info("[PINSPIDER] Start URL: %s" % self.start_urls[0])

        self.count_users = 0
        self.users_parsed = {}
        self.url_slugs_parsed = {}
        self.before = before
        self.re_url_extract = re.compile('url:(.*)')

    def parse(self, response):
        # fetches json representation of bookmarks instead of using css or xpath
        bookmarks = re.findall('bmarks\[\d+\] = (\{.*?\});', response.body.decode('utf-8'), re.DOTALL | re.MULTILINE)
        self.logger.info("[PINSPIDER] Bookmarks on this page: %d" % len(bookmarks))

        current_user = json.loads(bookmarks[0])['author']

        user_in_dict = self.users_parsed.get(current_user)
        if user_in_dict is None:
            self.count_users += 1
            self.users_parsed[current_user] = 1
        else:
            # Count pages for user
            self.users_parsed[current_user] += 1

        for b in bookmarks:
            bookmark = json.loads(b)
            if bookmark['url_slug'] in self.url_slugs_parsed:
                self.logger.info("[PINSPIDER URL %s has already been parsed." % bookmark['url_slug'])
            else:
                yield from self.parse_bookmark(bookmark)

        # Get bookmarks in previous pages
        previous_page = response.css('a#top_earlier::attr(href)').extract_first()
        if previous_page:
            previous_page = response.urljoin(previous_page)
            self.logger.info("[PINSPIDER] Fetching previous page: %s" % previous_page)
            yield scrapy.Request(previous_page, callback=self.parse)

    def parse_bookmark(self, bookmark):
        pin = PinItem()

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

        self.crawler.stats.inc_value('pin_count')

        yield pin
        if self.settings.get('PARSE_EXTERNAL_LINKS'):
            yield scrapy.Request(pin['url'], callback=self.parse_external_page, meta={'url_slug': pin['url_slug']}, priority=0)

        yield scrapy.Request('https://pinboard.in/url:' + pin['url_slug'], callback=self.parse_url_slug, priority=0)

    def parse_url_slug(self, response):
        url_slug = UrlSlugItem()

        if response.body:
            soup = BeautifulSoup(response.body, 'html.parser')

            self.crawler.stats.inc_value('url_slug_count')

            pin_url = soup.find('a', href=re.compile('^https?://'))['href']
            tagcloud = soup.find_all("div", id="tag_cloud")
            all_tags = [element.get_text() for element in tagcloud[0].find_all(class_='tag')]

            users = soup.find_all("div", class_="bookmark")
            user_list = [re.findall('/u:(.*)/t:', element.a['href'], re.DOTALL) for element in users]
            user_list_flat = sum(user_list, []) # Change from list of lists to list

            url_slug['url_slug'] = re.findall('url:(.*)', response.url)[0]
            url_slug['url'] = response.url
            url_slug['pin_url'] = pin_url
            url_slug['user_list'] = user_list_flat
            url_slug['user_list_length'] = len(user_list_flat)
            url_slug['all_tags'] = all_tags
            url_slug['url_slug_fetch_date'] = datetime.datetime.utcnow().isoformat()

            yield url_slug
            for user in user_list_flat:
                if user in self.users_parsed:
                    self.logger.info("[PINSPIDER] User %s already parsed." % user)
                else:
                    yield scrapy.Request('https://pinboard.in/u:%s/before:%s' % (user, self.before), callback=self.parse)

    def parse_external_page(self, response):
        external_page = PageItem()

        external_page['page_url'] = response.url
        external_page['page_url_slug'] = response.meta['url_slug']
        external_page['page_fetch_date'] = datetime.datetime.utcnow().isoformat()
        external_page['page_code'] = response.status
        external_page['page_content'] = ''
        external_page['page_content_size'] = 0

        self.crawler.stats.inc_value('external_pages_count')

        if (response.url[-4:] != '.pdf') and response.body:
            soup = BeautifulSoup(response.body, 'html.parser')
            # http://stackoverflow.com/questions/22799990/beatifulsoup4-get-text-still-has-javascript
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            external_page['page_content'] = text
            external_page['page_content_size'] = len(external_page['page_content'])

        yield external_page
