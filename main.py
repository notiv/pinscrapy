
# Script to use for debugging scrapy within PyCharm
from scrapy import cmdline
cmdline.execute("scrapy crawl pinboard -a user=Evil.Knees".split())
