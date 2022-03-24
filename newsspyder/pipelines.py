from sqlalchemy.orm import sessionmaker
from scrapy.exceptions import DropItem
from newsspyder.models import News, db_connect, create_table
from datetime import datetime

'''
Sets default values of fields which where not found.
'''
class DefaultValuesPipeline(object):

    def process_item(self, item, spider):
        
        item.setdefault('paywall', False)

        for field in item.fields:
            if field == 'date':
                # set default value of the publication date to a value in far 
                # distant past for an easy identification in the future analysis.
                item.setdefault(field, datetime.strptime("1800-12-17T17:27:11+01:00", '%Y-%m-%dT%X%z'))
            else:
                item.setdefault(field, 'NULL')

        return item

'''
Checks if the title and the link of the articles where scraped. Otherwise
an exception is raised.
'''
class IntegrityPipeline(object):
    def process_item(self, item, spider):
        important_fields = ['title', 'link']
        for field in important_fields:
            if item[field] == 'NULL':
                raise DropItem("Incomplete item found: %s" % item["link"])
        return item

'''
Saves the news items in the database.
'''
class SaveNewsPipeline(object):
    def __init__(self):
        #Initializes database connection and sessionmaker
        engine = db_connect()
        create_table(engine)
        self.Session = sessionmaker(bind=engine)


    def process_item(self, item, spider):
        # Save news in the database
        session = self.Session()
        news = News()
        news.title = str(item["title"])
        news.author = str(item["author"])
        news.date = item["date"]
        news.link = str(item["link"])
        news.journal = str(item["journal"])
        news.text = str(item["text"])
        news.processed_text = str(item["processed_text"])
        news.meta = str(item["meta"])

        try:
            session.add(news)
            session.commit()

        except:
            session.rollback()
            raise

        finally:
            session.close()

        return item