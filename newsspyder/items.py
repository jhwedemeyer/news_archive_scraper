# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join, Compose
import re
from datetime import datetime
import w3lib.html


'''
Collection of methods to process the scraped article informations like
title, text, date, etc.
'''

def remove_quotes(text):
    # strip the unicode quotes
    return text.strip(u'\u201c'u'\u201d')

def remove_multi_space(text):
    return re.sub(' +',' ', text)

def remove_newline(text):
    return text.replace('\n','')

def remove_soft_hiphen(text):
    return text.replace('\xad','')

def remove_no_break_space(text):
    return text.replace('\xa0', ' ')

def concat_text(text):
    return ''.join(text)

def convert_date(text):
    # convert string 19 Feb 2021 15:20:00 +0100 to Python date
    return datetime.strptime(text, '%d %b %Y %X %z')

def convert_date2(text):
    # convert string 'Tue, 23 Feb 2021 15:33:16 +0100' to Python date
    return datetime.strptime(text, '%a, %d %b %Y %X %z')

def convert_date3(text):
    # convert string 'Tue, 23 Feb 2021 17:17:18 GMT' to Python date
    return datetime.strptime(text, '%a, %d %b %Y %X %Z')

def convert_date4(text):
    # 2021-12-17T17:27:11+01:00
    return datetime.strptime(text, '%Y-%m-%dT%X%z')

def join_and_skip_first(text):
    return remove_multi_space(' '.join(text[1:]))

def remove_prefix(text):
    if len(text) == 1: # Case 1: only plaintext no href
        text = text[0].split(' ')
        if text[0] == "Von": # Case 1.1: Format: "Von Max Mustermann, Stadt"
            text = ' '.join(text[1:])
            text = text.split(',')
            return text[0]
        elif text[0] == "Kommentar": # Case 1.2: Format: "Kommentar von Max Mustermann, Stadt"
            text = ' '.join(text[2:])
            text = text.split(',')
            return text[0]
    elif len(text) == 2: # Case 2: ['Von', 'Max Mustermann, Stadt'] 
        text = text[1]
        text = text.split(',')
        return text[0]
    elif len(text) > 2: # Case 3: Format: "['Von', 'style_bla_bla', 'Max Mustermann', 'Stadt']"
        return text[2]

def entry_exists(text):
    if len(text) == 0:
        return [False]
    else :
        return [True]

'''
NewsLoader and NewsItem classes
One NewsItem class per journal
'''    

class NewsLoader(ItemLoader):
    default_output_processor = TakeFirst()
    

class NewsItem(Item):
    title = Field()
    author = Field()
    date = Field()
    journal = Field()
    link = Field()
    text = Field()
    processed_text = Field()
    paywall = Field() 
    meta = Field()

class SpiegelNewsItem(NewsItem):
    date = Field(input_processor=MapCompose(convert_date4))
    text = Field(
        input_processor=MapCompose(remove_newline, remove_soft_hiphen, remove_quotes),
        output_processor=Join()
        )
    
class ZeitNewsItem(NewsItem):
    date = Field(input_processor=MapCompose(convert_date4))
    text = Field(
        input_processor=MapCompose(remove_newline, remove_soft_hiphen, remove_quotes, remove_multi_space),
        output_processor=Join()
        )
        
class WeltNewsItem(NewsItem):
    date = Field(input_processor=MapCompose(convert_date4))
    text = Field(
        input_processor=MapCompose(w3lib.html.remove_tags, remove_newline, remove_soft_hiphen, remove_quotes, remove_multi_space),
        output_processor=Join()
        )

class TagesspiegelNewsItem(NewsItem):
    date = Field(input_processor=MapCompose(convert_date4))
    title = Field( 
        input_processor=MapCompose(remove_multi_space),
        output_processor=Join()
        )
    text = Field(
        input_processor=MapCompose(remove_newline, remove_multi_space, remove_soft_hiphen, remove_quotes, remove_no_break_space),
        output_processor=Join()
        )
    paywall = Field(input_processor=Compose(entry_exists))      



