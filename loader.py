import datetime

from google.appengine.ext import db
from google.appengine.tools import bulkloader

from models import Deadline, Book

class DeadlineLoader(bulkloader.Loader):
  def __init__(self):
    bulkloader.Loader.__init__(self, 'Deadline',
        [('book', lambda b: Book.get_by_key_name(b)),
         ('starts_on', lambda d: datetime.datetime.strptime(d, "%m/%d/%Y").date()),
         ('ends_on', lambda d: datetime.datetime.strptime(d, "%m/%d/%Y").date()),
         ('start_page', int),
         ('page', int),
         ('start_location', int),
         ('location', int)
        ])

loaders = [DeadlineLoader]
