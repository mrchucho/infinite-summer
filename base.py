#
# Copyright 2008 Ralph M Churchill
#

import logging
import sys
import traceback
import os
import types
import re
import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import mail
from google.appengine.ext.db import BadKeyError,Timeout
from google.appengine.runtime import DeadlineExceededError

class Http404(Exception):
  def __init__(self,value="Not Found"):
    self.value = value
  
  def __str__(self):
    return repr(self.value)

class BaseHandler(webapp.RequestHandler):
  TEMPLATE_PATH = os.path.join(os.path.dirname(__file__),'templates')
  __ERROR       = os.path.join(TEMPLATE_PATH,'error.html')

  @property
  def memcache_prefix(self):
    return os.getenv("CURRENT_VERSION_ID")

  """ Handle un-handled exceptions """
  def handle_exception(self,exception,debug_mode=False):
    if type(exception) is Http404:
      self.response.set_status(404)
      self.render_template(self.__ERROR,{'header':"Not Found",
        'detail':"Sorry, we couldn't find your document."})
    elif type(exception) in (Timeout,DeadlineExceededError):
      self.response.set_status(500)
      self.render_template(self.__ERROR,{'header':"Server Error",
        'detail':"Sorry, we are experiencing unusually high load. Please try again."})
    else:
      msg = 'Unhandled Exception: '.join(traceback.format_exception(*sys.exc_info()))
      logging.error(msg)
      mail.send_mail(sender="churchillrm@gmail.com",to="churchillrm@gmail.com",subject="Unhandled Exception",body=msg)
      self.response.set_status(500)
      self.render_template(self.__ERROR,{'header':"Server Error",
        'detail':"An unexpected error occurred. Please try again."})

  def get_object_or_404(self,object_class,object_id):
    if not object_id:
      raise Http404
    else:
      try:
        object = object_class.get(object_id)
      except BadKeyError:
        logging.error("Bad Key: %s" % object_id)
        raise Http404
      if not object:
        raise Http404
      else:
        return object

  def get_object_by_key_or_404(self,object_class,object_key):
    if not object_key:
      raise Http404
    else:
      try:
        object = object_class.get_by_key_name(object_key)
      except BadKeyError:
        logging.error("Bad Key: %s" % object_key)
        raise Http404
      if not object:
        raise Http404
      else:
        return object

  def render_template(self,template_name,context={}):
    self.response.out.write(template.render(template_name,context))

  def get_int_param(self, param):
    value = self.request.get(param, None)
    if value:
      value = int(re.sub('\D', '', value)) 
    else:
      value = None
    return value

  def get_date_param(self, param):
    value = self.request.get(param, None)
    if value:
      year, month, day = map(lambda x: int(x), value.split("/"))
      value = datetime.date(year, month, day)
    else:
      value = None
    return value

  def is_ajax(self):
    return self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'

  def wants_json(self):
    return 'application/json' in self.request.headers.get('Accept','').split(',')

  def set_cookie(self, name, value):
    self.response.headers.add_header('Set-Cookie','%s=%s' % (name, value))
