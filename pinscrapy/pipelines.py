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

class PinscrapyPipeLineS3(object):

    def __init__(self):
        self.s3client = None
        self.bucket_name = None

    def open_spider(self, spider):
        import boto3
        from scrapy.conf import settings

        self.s3client = boto3.client('s3')
        self.bucket_name = spider.settings.get('AWS_BUCKET_NAME')

        # Check that the bucket exists, otherwise create it
        if not any(b['Name'] == self.bucket_name for b in self.s3client.list_buckets()['Buckets']):
            self.s3client.create_bucket(Bucket=self.bucket_name)
        else:
            spider.logger.info('[PINSPIDER] Bucket %s exists' % self.bucket_name)

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        itm_type = item_type(item)

        if itm_type == 'pin':
            author = item['author']
            url_slug = item['url_slug']

            object_key = 'users/%s_%s_%s.jl' %(itm_type, author, url_slug)
            object_content = json.dumps(dict(item)) + "\n"
            resp = self.s3client.put_object(Bucket=self.bucket_name, Key=object_key, Body=object_content)
            print(resp)
        elif itm_type == 'urlslug':
            url_slug = item['url_slug']

            object_key = 'url_slugs/%s_%s.jl' %(itm_type, url_slug)
            object_content = json.dumps(dict(item)) + "\n"
            self.s3client.put_object(Bucket=self.bucket_name, Key=object_key, Body=object_content)

        return item


