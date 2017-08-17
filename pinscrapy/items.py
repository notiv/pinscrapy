# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class PinscrapyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    id = scrapy.Field()
    url = scrapy.Field()
    url_id = scrapy.Field()
    url_slug = scrapy.Field()
    url_count = scrapy.Field()
    title = scrapy.Field()
    created_at = scrapy.Field()
    pin_fetch_date = scrapy.Field()
    tags = scrapy.Field()  # array of tags
    author = scrapy.Field()

    # fields that we get when parsing the
    # url_slug (e.g. https://pinboard.in/url:f81a7954a8ab701aa47ddaef236d90fea167dfae/)
    user_list = scrapy.Field()  # array of users who have saved this pin as well
    user_list_length = scrapy.Field() # number of users who have saved this pin as well
    all_tags = scrapy.Field()  # array of tags from all users


    # JSON that's on pinboard results page
    # {
    # "id":"95383442",
    # "url":"http:\/\/lovelycharts.com\/",
    # "url_id":"112815",
    # "author":"lfcipriani",
    # "created":"2010-10-09 01:31:25",
    # "description":"",
    # "title":"Lovely Charts | Free online diagram software - Flowchart & process diagram, Network diagram, BPMN diagrams, Sitemap, Organisation chart, Wireframe, business drawing software",
    # "slug":"2c72bdd86db1",
    # "toread":"0",
    # "cached":null,
    # "code":null,
    # "private":"0",
    # "user_id":"60410",
    # "snapshot_id":null,
    # "updated":"2011-02-14 17:52:29",
    # "in_collection":null,
    # "sertags":",application,graph,graphics,chart,design,diagram,diagramming,flowchart,tool,visualization,",
    # "source":"7",
    # "tags":[
    # "application",
    # "graph",
    # "graphics",
    # "chart",
    # "design",
    # "diagram",
    # "diagramming",
    # "flowchart",
    # "tool",
    # "visualization"
    # ],
    # "author_id":"60410",
    # "url_slug":"c9f75b6d4b90340713effa1ddac4f876778c4f1b",
    # "url_count":"145"
    # };
