#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from newsspyder.models import News, db_connect, create_table
from sqlalchemy.orm import sessionmaker
import logging
from itertools import compress


'''
Filter to check if items are already in db and do not need to be scraped.
'''
class DuplicateFilter():
    
    """
    Initializes database connection and sessionmaker.
    """
    def __init__(self):
        engine = db_connect()
        create_table(engine)
        self.Session = sessionmaker(bind=engine)
        logging.info("****DuplicatesFilter: database connected****")


    '''
    Checks is a single url is in the db
    '''
    def check_for_duplicate(self, session, url, debugging=False):
        exist_news = session.query(News).filter_by(link = url).first()
        if exist_news is not None:  # the article exists
            if debugging:
                logging.info("DuplicateFilter: Found duplicate article "+ url)
            return False
        else:
            return True
        
    '''
    Checks if a list of urls is in the db
    '''
    def check_list_for_duplicates(self, url_list, debugging=False):
        session = self.Session()
        url_mask = [self.check_for_duplicate(session, url, debugging) for url in url_list]
        filtered_urls = list(compress(url_list, url_mask))
        session.close()
        return filtered_urls
