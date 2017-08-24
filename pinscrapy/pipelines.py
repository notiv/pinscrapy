# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json

def item_type(item):
    return type(item).__name__.replace('Item','').lower()  # UrlSlugItem => urlslug

class PinscrapyPipeline(object):

    def process_item(self, item, spider):
        itm_type = item_type(item)

        if itm_type == 'pin':
            author = item['author']
            url_slug = item['url_slug']
            self.file = open('users/%s_%s_%s.jl' %(itm_type, author, url_slug), 'w')
            line = json.dumps(dict(item)) + "\n"
            self.file.write(line)
            self.file.close()
        elif itm_type == 'urlslug':
            url_slug = item['url_slug']
            self.file = open('url_slugs/%s_%s.jl' %(itm_type, url_slug), 'w')
            line = json.dumps(dict(item)) + "\n"
            self.file.write(line)
            self.file.close()

        return item

