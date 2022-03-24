#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import scrapy
from newsspyder.items import WeltNewsItem, NewsLoader
import logging
import json
import pandas as pd
from newsspyder.duplicate_filter import DuplicateFilter

'''
Spider to scrape all available Welt articles.
'''
class WeltSpider(scrapy.Spider):
    name = "welt"
    itertag = "item"
    
    date_range = pd.date_range(start='1/1/1995', end='28/12/2021')
    start_urls = ["https://www.welt.de/schlagzeilen/nachrichten-vom-"+str(date.day)+"-"+str(date.month)+"-"+str(date.year)+".html" for date in date_range]

    '''
    Parse archiv page for artile urls. Follow them.
    Check if article is already in db.
    '''
    def parse(self, response):
        logging.info("crawl archiv")
        
        # get articles urls
        article_urls = response.css('div.text div.article a ::attr(href)').getall()
        article_urls = list(set(article_urls)) # remove duplicates
        
        # check if article url is in db
        url_filter = DuplicateFilter()
        article_urls = url_filter.check_list_for_duplicates(article_urls)
        
        # follow all urls not in db
        yield from response.follow_all(article_urls, callback=self.parse_article)
        
        
    '''
    Parse article and save it as NewsItem.
    '''
    def parse_article(self, response):
        logging.info("crawl article "+ response.url)
        
        # get structured article information       
        structured_data = json.loads(response.css("script[type='application/ld+json'] ::text").get())
        
        # extract relevant informations and save them
        loader = NewsLoader(item=WeltNewsItem(), response=response)
        loader.add_value('meta', structured_data)
        loader.add_value('title', structured_data['headline'])
        loader.add_value('journal', self.name)
        loader.add_value('author', structured_data['author'])
        try:
            loader.add_value('paywall', not structured_data['isAccessibleForFree'])
        except KeyError:
            loader.add_value('paywall', "NULLL")

        loader.add_value('date', structured_data['datePublished'])
        loader.add_value('link', response.url)
        loader.add_value('text', structured_data['articleBody'])

        yield loader.load_item()

        
