#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import scrapy
from newsspyder.items import ZeitNewsItem, NewsLoader
import logging
import json
from scrapy.http import Request
from newsspyder.duplicate_filter import DuplicateFilter
from pathlib import Path

'''
Spider to scrape all available Zeit articles.
'''
class ZeitSpider(scrapy.Spider):
    name = "zeit"
    start_urls = ['https://www.zeit.de/'+ str(year) +'/index' for year in range(1946,2022)]
    itertag = "item"
    
    # zeit cookie: fill in to get fulltext access
    premium_cookie = {
	}

    '''
    Use premium cookie when doing the web request
    '''
    def start_requests(self):
        return [Request(url, dont_filter=True, cookies=self.premium_cookie, callback=self.parse_archiv) for url in self.start_urls]
    
    '''
    Parse yearly archiv for magazin urls. Follow them.
    Check before if magazin url is already fully scraped.
    '''
    def parse_archiv(self, response):
        logging.info("crawl archiv")
        
        # get magazin urls
        magazin_urls = response.css('article a ::attr(href)').getall()

        # check if they are already scraped        
        my_file = Path(self.name+"_finished_urls.txt")
        if my_file.is_file():
            f = open(my_file.name, "r")
            finished_urls = f.read().splitlines()
            f.close()
        else:
            f = open(my_file.name, "a")
            f.write("")
            f.close()
            finished_urls = []
            
        # create list with not yet fully scraped magazins
        left_over_urls = set(magazin_urls) - set(finished_urls)
        logging.info("finished urls: " + str(len( set(magazin_urls) -  left_over_urls)) + "/" + str(len(magazin_urls)) )
        magazin_urls = list(left_over_urls)
        logging.info(magazin_urls)
        
        # follow the urls
        yield from response.follow_all(magazin_urls, callback=self.parse_magazin, cookies=self.premium_cookie)
        
    
    '''
    Parse magazin for article urls. Follow them.
    Check if the articles are already in db.
    '''
    def parse_magazin(self, response):
        logging.info("crawl magazin")
        
        # get article urls
        article_urls = response.css('article div a ::attr(href)').getall()
        article_urls = list(set(article_urls)) # remove duplicates
        
        # check if they are already scraped
        url_filter = DuplicateFilter()
        article_urls = url_filter.check_list_for_duplicates(article_urls,  debugging=True)

        # if all articles are scraped, mark magazin as finished        
        if len(article_urls) == 0:
            logging.info("Finished magazin: " + response.url)
            f = open(self.name+"_finished_urls.txt", "a")
            f.write(response.url + "\n")
            f.close()
        
        # follow links
        yield from response.follow_all(article_urls, callback=self.parse_article, cookies=self.premium_cookie)
     
    '''
    Parse article and save it as NewsItem.
    '''
    def parse_article(self, response):
        logging.info("crawl article "+ response.url)
        
        # check if article has mulitple pages. if so, access the full views
        multi_page_link = response.css("li.article-pager__all a ::attr(href)").get()
        if multi_page_link:
            yield Request(multi_page_link, callback=self.parse_article, dont_filter=True, cookies=self.premium_cookie)

        else:
            # get structured article information       
            structured_data = json.loads(response.css("head script[type='application/ld+json'] ::text").getall()[-1])
            
            # extract relevant informations and save them
            loader = NewsLoader(item=ZeitNewsItem(), response=response)
            loader.add_value('meta', structured_data)
            loader.add_value('title', structured_data['headline'])
            loader.add_value('journal', self.name)
            loader.add_value('author', structured_data['author'])
            try:
                loader.add_value('paywall', not structured_data['isAccessibleForFree'])
            except KeyError:
                loader.add_value('paywall', "NULL")

            loader.add_value('date', structured_data['datePublished'])
            loader.add_value('link', response.url)
            loader.add_css('text','p.article__item ::text')
            yield loader.load_item()

        
