import re
import logging

class RankedBarChart(object):
  def __init__(self, progress):
    self.progress = progress
    self.chd = ",".join(map(lambda p: "%.01f" % p.progress, self.progress))
    self.chxl = "|".join(map(lambda p: re.sub('@.*$', '', p.reader.nickname()), reversed(self.progress)))

  # TODO set chart margins
  # TODO set chart marker for current deadline progress %
  def url(self):
    prefix = "http://chart.apis.google.com/chart?cht=bhs&chco=4D89F9,C6D9FD&chs=400x300&chm=N%20*f0*%,000000,0,-1,11&chxt=y"
    return "%s&chd=t:%s&chxl=0:|%s|" % (prefix, self.chd, self.chxl)
