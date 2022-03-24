#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import scrapy
from newsspyder.items import TagesspiegelNewsItem, NewsLoader
from pathlib import Path
import logging
from newsspyder.duplicate_filter import DuplicateFilter

'''
Spider to scrape all available Tagesspiegel articles.
'''
class TagesspiegelSpider(scrapy.Spider):
    name = "tagesspiegel"
    itertag = "item"
    finished_urls_file = Path(name+"_finished_urls.txt")
    finished_urls = []
    
    start_urls = ["https://www.tagesspiegel.de/suchergebnis/artikel/?search-fromday=1&search-frommonth=1&search-fromyear="+str(year)+"&search-today=31&search-tomonth=12&search-toyear=" + str(year) for year in range(1996,2022)]
    
    '''
    Spider constructor to load the list with already fully scraped years
    '''
    def __init__(self, *a, **kw):
        super(TagesspiegelSpider, self).__init__(*a, **kw)
        
        if self.finished_urls_file.is_file():
            f = open(self.finished_urls_file.name, "r")
            self.finished_urls = f.read().splitlines()
            f.close()
        else:
            f = open(self.finished_urls_file.name, "a")
            f.write("")
            f.close()
        
    '''
    Parse the yearly archiv for multiple pages. Follow the page-links.
    Check if the pages are already complety scraped
    '''
    def parse(self, response):
        logging.info("crawl year archiv")
        
        # generate the page urls from the scraped max page number
        max_page_number = int(response.css("li.hcf-paging-forward:last-child ::attr(title)").get().split()[1])
        page_urls = [response.url + "&p9049616=" + str(page) for page in range(1,max_page_number+1)]
        
        # remove pages which are already fully scraped
        missing_pages = list(set(page_urls) - set(self.finished_urls))
                        
        yield from response.follow_all(missing_pages, callback=self.parse_page)

    '''
    Parse the pages of the yearly archiv for article urls. Follow them.
    Check if the article URLs are already in the DB.
    '''
    def parse_page(self, response):
        logging.info("crawl page")
        
        # get article urls
        article_urls = response.css('li.hcf-teaser > h2 > a ::attr(href)').getall()
        article_urls = ["https://www.tagesspiegel.de" + url for url in article_urls]
        
        # check if the article urls are in the db
        url_filter = DuplicateFilter()
        article_urls = url_filter.check_list_for_duplicates(article_urls, debugging=False)
        
        # if all articles are scraped, mark page as finished
        if len(article_urls) == 0:
            logging.info("Finished page: " + response.url)
            f = open(self.finished_urls_file.name, "a")
            f.write(response.url + "\n")
            f.close()
        
        yield from response.follow_all(article_urls, callback=self.parse_article)

    '''
    Parse article and save it as NewsItem.
    '''
    def parse_article(self, response):
        logging.info("crawl article: " + response.url)
        
        # extract relevant informations and save them
        loader = NewsLoader(item=TagesspiegelNewsItem(), response=response)
        loader.add_css('text','div.ts-article-body p ::text')
        loader.add_css('author','address.ts-authors span a ::text')
        loader.add_css('paywall', 'header h1 svg')
        loader.add_value('link', response.url)
        loader.add_value('journal', self.name)
        loader.add_css("title","h1 ::text")
        loader.add_css("date","time.ts-time ::attr(datetime)")
        
        yield loader.load_item()
        
        
