#!/usr/bin/env python

import os
import wsgiref.handlers
import logging

from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.api import mail

from base import BaseHandler
from models import Book, Deadline, Entry, Progress
from chart import RankedBarChart

class BookDeadlineHandler(BaseHandler):
  DEADLINES_TEMPLATE = os.path.join(BaseHandler.TEMPLATE_PATH, 'deadlines.html')
  DEADLINE_TEMPLATE = os.path.join(BaseHandler.TEMPLATE_PATH, 'deadline.html')

  # admin_only
  def get(self, book_slug, deadline_key = None):
    book = self.get_object_by_key_or_404(Book, book_slug)
    if not deadline_key:
      deadlines = book.deadline_set.order("ends_on")
      self.render_template(self.DEADLINES_TEMPLATE, {'book': book, 'deadlines': deadlines})
    else:
      deadline = self.get_object_or_404(Deadline, deadline_key)
      self.render_template(self.DEADLINE_TEMPLATE, {'book': book, 'deadline': deadline})

  # admin_only
  def post(self, book_slug, arg):
    book = self.get_object_by_key_or_404(Book, book_slug)
    deadline = Deadline(book      = book,
                        starts_on = self.get_date_param('starts_on'),
                        ends_on   = self.get_date_param('ends_on'),
                        page      = self.get_int_param('page'),
                        location  = self.get_int_param('location'),
                        start_page= self.get_int_param('start_page'),
                        start_location= self.get_int_param('start_location'))
    deadline.put()
    self.redirect('/admin/books/%s/deadlines/%s/' % (book.slug, deadline.key()))


class BookAdminHandler(BaseHandler):
  BOOKS_TEMPLATE = os.path.join(BaseHandler.TEMPLATE_PATH, 'books_edit.html')
  BOOK_TEMPLATE = os.path.join(BaseHandler.TEMPLATE_PATH, 'book_edit.html')

  # admin_only
  def get(self, book_slug = None):
    if not book_slug:
      books = Book.all()
      self.render_template(self.BOOKS_TEMPLATE,{'books': books})
    else:
      book = self.get_object_by_key_or_404(Book, book_slug)
      self.render_template(self.BOOK_TEMPLATE,{'book': book})

  # admin_only
  def post(self, arg):
    book = Book(title     = self.request.get('title', None), 
                pages     = self.get_int_param('pages'),
                locations = self.get_int_param('locations'))
    book.put()
    self.redirect('/admin/books/%s/' % book.slug)


class BookHandler(BaseHandler):
  BOOKS_TEMPLATE = os.path.join(BaseHandler.TEMPLATE_PATH, 'books.html')
  BOOK_TEMPLATE = os.path.join(BaseHandler.TEMPLATE_PATH, 'book.html')

  def get(self, book_slug = None):
    if not book_slug:
      books = Book.all()
      self.render_template(self.BOOKS_TEMPLATE,{'books': books})
    else:
      book = self.get_object_by_key_or_404(Book, book_slug)
      self.render_template(self.BOOK_TEMPLATE,{'book': book})


class EntryHandler(BaseHandler):

  def get(self):
    self.redirect("/")

  def post(self):
    page = self.get_int_param("page")
    location = self.get_int_param("location")
    if page or location:
      try:
        entry = Entry.create(book     = Book.get_by_key_name("infinite-summer"),
                             reader   = users.get_current_user(),
                             page     = page,
                             location = location)
        Progress.create(entry)
      except ValueError, error:
        self.set_cookie("flash_message", error)
    else:
      self.set_cookie("flash_message", "Please specify a page.")

    if self.wants_json():
      pass
    else:
      self.redirect("/")


class MainHandler(BaseHandler):
  INDEX_TEMPLATE = os.path.join(BaseHandler.TEMPLATE_PATH, 'index.html')

  def get(self):
    logging.debug("APP_ID: %s" % os.environ['APPLICATION_ID'])
    logging.debug("Subdomain: %s" % self.subdomain())
    user = users.get_current_user()
    book = Book.get_by_key_name('infinite-summer')
    entries = book.entry_set.filter('reader =', user).order('-created_at').fetch(10)
    progress = book.progress_set.filter('reader =', user).get()
    graph = ','.join(book.progress_stats_for_reader(user))
    self.render_template(self.INDEX_TEMPLATE, {
      'user': user,
      'book': book,
      'entries': entries,
      'progress': progress,
      'current_deadline': book.current_deadline(),
      'top_ten': RankedBarChart(book.top_ten_readers()),
      'bottom_ten': RankedBarChart(book.bottom_ten_readers()),
      'top_ten_this_week': RankedBarChart(book.top_ten_readers_this_week()),
      'bottom_ten_this_week': RankedBarChart(book.bottom_ten_readers_this_week()),
      'readers_today': book.readers_today(),
      'graph': graph,
      'login_url': users.create_login_url("/"),
      'finishers': book.finished_readers(),
      })


class ContactHandler(BaseHandler):
  CONTACT_TEMPLATE = os.path.join(BaseHandler.TEMPLATE_PATH, 'contact.html') 

  def get(self):
    self.render_template(self.CONTACT_TEMPLATE)

  def post(self):
    body = """
    From: %s
    Subject: %s
    Body: 
    %s
    """ % tuple(map(lambda r: self.request.get(r, None), ['from', 'subject', 'body']))
    mail.send_mail_to_admins(sender  = "churchillrm@gmail.com",
                             subject = "Infinite Summer Contact",
                             body    = body)
    self.set_cookie("flash_message", "Your message was successfully sent.")
    self.redirect("/")

def main():
  if BaseHandler.DEVELOPMENT:
    logging.getLogger().setLevel(logging.DEBUG)
  application = webapp.WSGIApplication([
    ('/admin/books/?([^/]*)/deadlines/?([^/]*)/?', BookDeadlineHandler),
    ('/admin/books/?([^/]*)/?', BookAdminHandler),
    ('/books/?([^/]*)/?', BookHandler),
    ('/entries/?', EntryHandler),
    ('/contact/?', ContactHandler),
    ('/', MainHandler),
    ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
