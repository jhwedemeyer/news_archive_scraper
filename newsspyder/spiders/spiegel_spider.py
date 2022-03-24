#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import scrapy
from newsspyder.items import SpiegelNewsItem, NewsLoader
import logging
import json
from scrapy.http import Request
from newsspyder.duplicate_filter import DuplicateFilter
from pathlib import Path

'''
Spider to scrape all available Spiegel magazins.
'''
class SpiegelSpider(scrapy.Spider):
    name = "spiegel"
    start_urls = ['https://www.spiegel.de/spiegel/print/index-1994.html']
    itertag = "item"
    
    # spiegel plus cookie: fill in to get fulltext access for plus articles
    premium_cookie = {
	}

    '''
    Parser the start_url for archiv-links. Follow them.
    '''
    def parse(self,response):
        # get archiv urls
        archiv_urls = response.css('div.swiper-container:nth-child(3) > ul:nth-child(3) a ::attr(href)').getall()
        logging.info(archiv_urls)
        yield from response.follow_all(archiv_urls, callback=self.parse_archiv)
        
    '''
    Parser the archiv for magazins-links. Follow them.
    Check if the magazin-links is in the spiegel_finished_urls.txt 
    and already completly scraped.
    '''
    def parse_archiv(self, response):
        logging.info("crawl archiv")
        
        # get magazin urls
        magazin_urls = response.css('.lg\:pb-28 > div > a ::attr(href)').getall()

        # check if magazin is already completly scraped
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

        left_over_urls = set(magazin_urls) - set(finished_urls)
        logging.info("finished urls: " + str(len( set(magazin_urls) -  left_over_urls)) + "/" + str(len(magazin_urls)) )
        
        # follow the magazin-links which are not finished yet
        magazin_urls = list(left_over_urls)
        logging.info(magazin_urls)
        yield from response.follow_all(magazin_urls, callback=self.parse_magazin)
    
    '''
    Parse the magazins for article-links. Follow them.
    Check before if the article is already in the DB. 
    If all articles are in the DB, then mark the magazin as finished in spiegel_finished_urls.txt 
    '''
    def parse_magazin(self, response):
        logging.info("crawl magazin")
        
        # get article urls
        article_urls = response.css('article a ::attr(href)').getall()
        article_urls = list(set(article_urls)) # remove duplicates
        
        # check if the articles are already scraped
        url_filter = DuplicateFilter()
        article_urls = url_filter.check_list_for_duplicates(article_urls, debugging=True)
        
        # if all articles are scraped mark the magazin as finished
        if len(article_urls) == 0:
            logging.info("Finished magazin: " + response.url)
            f = open(self.name+"_finished_urls.txt", "a")
            f.write(response.url + "\n")
            f.close()
        
        yield from response.follow_all(article_urls, callback=self.parse_article)
      
    '''
    Parse article and save it as NewsItem.
    If the article is behind a paywall, use the premium cookie to access it.
    '''
    def parse_article(self, response, logged_in = False):
        logging.info("crawl article "+ response.url + "logged in " + str(logged_in))
        
        # get structured article information       
        structured_data = json.loads(response.css("head script[type='application/ld+json'] ::text").get())
        
        # check for a paywall
        if not logged_in and not structured_data['@context' == 'NewsArticle']['isAccessibleForFree']:
            yield Request(response.url, callback=self.parse_article, dont_filter=True, cookies=self.premium_cookie, cb_kwargs=dict(logged_in=True))
      
        else:
            # extract relevant informations and save them
            loader = NewsLoader(item=SpiegelNewsItem(), response=response)
            loader.add_value('meta', structured_data['@context' == 'NewsArticle'])
            loader.add_value('title', structured_data['@context' == 'NewsArticle']['headline'])
            loader.add_value('journal', self.name)
            loader.add_value('author', structured_data['@context' == 'NewsArticle']['author'])
            loader.add_value('paywall', not structured_data['@context' == 'NewsArticle']['isAccessibleForFree'])
            loader.add_value('date', structured_data['@context' == 'NewsArticle']['datePublished'])
            loader.add_value('link', response.url)
            loader.add_css('text','article p ::text')
            yield loader.load_item()

        
