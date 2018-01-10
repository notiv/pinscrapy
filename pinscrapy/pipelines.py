# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json
import pymongo
import boto3
import s3fs
import pandas as pd
from fastparquet import write
from scrapy.conf import settings

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

class PinscrapyMongoPipeline(object):

    pin_collection_name = 'pins'
    urlslug_collection_name = 'urlslugs'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        if not self.db.get_collection(self.pin_collection_name):
            self.db.create_collection(self.pin_collection_name)
        if not self.db.get_collection(self.urlslug_collection_name):
            self.db.create_collection(self.urlslug_collection_name)

        # Create index (if none exists) to make updates faster
        self.db[self.pin_collection_name].create_index([('url_slug', pymongo.ASCENDING), ('author', pymongo.ASCENDING), ('create_at', pymongo.ASCENDING)])
        self.db[self.pin_collection_name].create_index([('author', pymongo.ASCENDING)])
        self.db[self.urlslug_collection_name].create_index([('url_slug', pymongo.ASCENDING)])

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        itm_type = item_type(item)

        if itm_type == 'pin':
            # self.db[self.pin_collection_name].insert_one(dict(item))
            # self.db[self.pin_collection_name].update({'url_slug': item['url_slug']}, {'$set': {'pin_fetch_date': item['pin_fetch_date']}}, upsert = True)
             self.db[self.pin_collection_name].update({'url_slug': item['url_slug']}, dict(item), upsert=True)
        elif itm_type == 'urlslug':
              self.db[self.urlslug_collection_name].update({'url_slug': item['url_slug']}, dict(item), upsert=True)
        return item

class PinscrapyPipelineLargeParquetFileS3(object):

    def __init__(self):
        self.s3 = s3fs.S3FileSystem()
        self.s3open = self.s3.open

        self.large_df_user = pd.DataFrame()
        self.large_df_urlslug = pd.DataFrame()
        self.bucket_name = None

    def open_spider(self, spider):
        self.bucket_name = spider.settings.get('AWS_BUCKET_NAME')

    def close_spider(self, spider):
        write('%s/user_%s.parq.gzip' % (self.bucket_name, spider.start_user), self.large_df_user, compression='GZIP', open_with=self.s3open)
        write('%s/url_slug_%s.parq.gzip' % (self.bucket_name, spider.start_user), self.large_df_urlslug, compression='GZIP', open_with=self.s3open)

    def process_item(self, item, spider):
        itm_type = item_type(item)

        if itm_type == 'pin':
            self.large_df_user = self.large_df_user.append(pd.DataFrame([dict(item)]), ignore_index = True)

        elif itm_type == 'urlslug':
            self.large_df_urlslug = self.large_df_urlslug.append(pd.DataFrame([dict(item)]), ignore_index = True)

        return item

