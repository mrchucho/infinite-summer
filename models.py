import re
import datetime
import logging

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import memcache

class Book(db.Model):
  title     = db.StringProperty(required=True)
  pages     = db.IntegerProperty(required=True)
  locations = db.IntegerProperty(required=True)
  slug      = db.StringProperty(required=True)

  CACHE_EXPIRY = 60*60

  def __init__(self, *args, **kwargs):
    if 'title' in kwargs:
      slug = re.sub('\W', '-', kwargs["title"]).lower()
      kwargs["key_name"] = slug
      kwargs["slug"] = slug
    db.Model.__init__(self, *args, **kwargs)

  def __str__(self):
    return self.title

  def current_deadline(self):
    return Deadline.current(self.deadline_set).get()

  def entry_vs_deadline(self, entry):
    if not entry:
      return -1
    deadline = self.current_deadline()
    logging.debug("%d < %d > %d" % (deadline.start_page, entry.page, deadline.page))
    if entry.page < deadline.start_page:
      return -1
    elif entry.page > deadline.page:
      return 1
    else:
      return 0

  def top_ten_readers(self):
    top_ten_readers = memcache.get("top_ten_readers")
    if not top_ten_readers:
      # top_ten_readers = self.progress_set.filter("updated_on IN =", self._this_week()).order('-progress').fetch(10)
      top_ten_readers = self.progress_set.order('-progress').fetch(10)
      memcache.set(key = "top_ten_readers", value = top_ten_readers, time = Book.CACHE_EXPIRY)
    return top_ten_readers

  def bottom_ten_readers(self):
    bottom_ten_readers = memcache.get("bottom_ten_readers")
    if not bottom_ten_readers:
      bottom_ten_readers = self.progress_set.order('progress').fetch(10)
      memcache.set(key = "bottom_ten_readers", value = bottom_ten_readers, time = Book.CACHE_EXPIRY)
    return bottom_ten_readers

  def progress_stats_for_reader(self, reader):
    return map(lambda e: str(self.entry_vs_deadline(e)), self.entry_set.filter('reader =', reader).order('created_at')) 

  def _this_week(self):
    date = datetime.date.today()
    prev = datetime.timedelta(days = -1)
    self.this_week = [date]
    while date.weekday() > 0:
      self.this_week.appen(date)
      date += prev
    return self.this_week

class Deadline(db.Model):
  book      = db.ReferenceProperty(Book, required=True)
  starts_on = db.DateProperty(required=True)
  ends_on   = db.DateProperty(required=True)
  page      = db.IntegerProperty(required=True)
  location  = db.IntegerProperty(required=True)
  start_page= db.IntegerProperty(required=True)
  start_location = db.IntegerProperty(required=True)

  @classmethod
  def current(cls, query, relative_to = datetime.date.today()):
    # I don't know how to chain these...
    return query.filter("ends_on >=", relative_to).order("ends_on")

  def percent_complete(self):
    return (float(self.page) / float(self.book.pages)) * 100.0
    
  def __str__(self):
    return "Page %d by %s" % (self.page, self.ends_on.strftime("%B %d, %Y"))


class Entry(db.Model):
  book       = db.ReferenceProperty(Book, required=True)
  reader     = db.UserProperty(required=True, auto_current_user_add=True)
  created_at = db.DateTimeProperty(required=True, auto_now_add=True)
  page       = db.IntegerProperty()
  location   = db.IntegerProperty()


class Progress(db.Model):
  book       = db.ReferenceProperty(Book, required=True)
  reader     = db.UserProperty(required=True, auto_current_user_add=True)
  last_entry = db.ReferenceProperty(Entry, required=True)
  progress   = db.FloatProperty()
  updated_at = db.DateTimeProperty(required=True, auto_now_add=True, auto_now=True)
  updated_on = db.DateProperty(required=True, auto_now_add=True, auto_now=True)

  @classmethod
  def create(cls, entry):
    keyname = "%s-%s" % (entry.book.slug, entry.reader)
    progress = cls(key_name   = keyname,
                   book       = entry.book,
                   last_entry = entry,
                   progress   = cls._overall(entry))
    return progress.put()

  def overall(self):
    if self.last_entry:
      return Progress._overall(self.last_entry)
    else:
      return 0.0

  def relative(self):
    if self.last_entry:
      return "%d/%d" % Progress._progress(self.last_entry)
    else:
      return "0/%d" % self.book.pages

  def status(self):
    return {
        0: "On Track",
        1: "Ahead of Schedule",
        -1: "Behind Schedule"
        }[self.book.entry_vs_deadline(self.last_entry)]

  @classmethod
  def _progress(cls, entry):
    if not entry:
      return (0, 0)
    if entry.page:
      return (entry.page, entry.book.pages)
    else:
      return (entry.location, entry.book.locations)

  @classmethod
  def _overall(cls, entry):
    my, book = cls._progress(entry)
    return (float(my) / float(book)) * 100.0

