#!/usr/bin/env python
#-*- coding: utf-8 -*-
'''
Dialog to show and organize logs written by e.g. QuickNXS.
The logformat should be:

[{Severity}] - {time} - <optional thread name> - {module}.py:{line}:{method} Info
...additional content...

'''

import time
import logging
from PyQt5.QtWidgets import QMainWindow, QTreeWidgetItem, QFileDialog
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QFileSystemWatcher, QObject, pyqtSignal
from .quicklog_window import Ui_MainWindow

class Logfile(QObject):
  entries=None
  curpos=0
  fname=None
  encoding='utf8'

  entriesUpdated=pyqtSignal(int, int)

  def __init__(self, filename, encoding='utf8'):
    QObject.__init__(self)

    self.entries=[]
    self.fname=filename
    self.encoding=encoding
    text=self.read_text()

    self.analyze_text(text)

    self.watch=QFileSystemWatcher([filename])
    self.watch.fileChanged.connect(self.update_text)
  
  def read_text(self):
    fh=open(self.fname, 'rb')
    fh.seek(self.curpos)
    text=fh.read()
    self.curpos=fh.tell()
    fh.close()
    text=unicode(text, encoding=self.encoding)
    return text

  def analyze_text(self, text):
    entry_texts=text.split(u'\n[')
    entry_texts=[u'['+item for item in entry_texts]
    entry_texts[0]=entry_texts[0][1:]

    for entry_text in entry_texts:
      if entry_text.strip()==u"":
        continue
      try:
        entry=LogEntry(entry_text)
      except ValueError:
        logging.warn('Error reading entry text "%s":'%entry_text, exc_info=True)
        continue
      self.entries.append(entry)
  
  def update_text(self):
    text=self.read_text()
    pre_update=len(self.entries)
    self.analyze_text(text)
    post_update=len(self.entries)
    self.entriesUpdated.emit(pre_update, post_update-1)

class LogEntry(object):
  severity=logging.INFO
  time=None
  thread=None
  source_file=None
  source_line=0
  source_method=None
  comment_info=u''
  comment_text=u''

  def __init__(self, text):
    '''
    :param unicode text: Line or liens of text in the logfile to analyze
    '''
    lines=text.split(u'\n', 1)
    map(unicode.strip, lines)

    if len(lines)==1:
      fline=lines[0]
      elines=u''
    else:
      fline, elines=lines

    fline_items=fline.split(' - ')
    if len(fline_items)==3:
      cline=fline_items[2]
    elif len(fline_items)==4:
      self.thread=fline_items[2].strip()
      cline=fline_items[3]
    else:
      raise ValueError, 'Unknown format in line %s'%fline

    self.severity=eval('logging.'+fline_items[0].strip(u' []'))
    self.time=time.strptime(fline_items[1].strip(), u'%Y-%m-%d %H:%M:%S,%f')

    filename, lineno, rest=cline.split(u':', 2)
    self.source_file=filename.strip()
    self.source_line=int(lineno)

    m, ci=rest.split(None, 1)
    self.source_method=m.strip()
    self.comment_info=ci.strip()

    self.comment_text=elines

  @property
  def stime(self):
    return time.asctime(self.time)

  @property
  def sseverity(self):
    return logging.getLevelName(self.severity)

  def __repr__(self):
    output='<LogEntry severity="%s" time="%s">'%(self.sseverity, self.stime)
    return output

class TreeWidgetTimeItem(QTreeWidgetItem):
  timecol=0
  timecode=0

  def __init__(self, items, timecol):
    self.timecode=items[timecol]
    items[timecol]=time.asctime(items[timecol])
    QTreeWidgetItem.__init__(self, items)
    self.timecol=timecol

  def __lt__(self, otherItem):
    column=self.treeWidget().sortColumn()
    if column==self.timecol:
      return self.timecode<otherItem.timecode
    else:
      return QTreeWidgetItem.__lt__(self, otherItem)


class QuicklogWindow(QMainWindow):
  logfile=None
  logfile_name=None

  def __init__(self, *args, **opts):
    QMainWindow.__init__(self, *args, **opts)
    self.ui=Ui_MainWindow()
    self.ui.setupUi(self)
    self.ui.logTree.sortByColumn(1, Qt.AscendingOrder)
    self.ui.logTree.setColumnWidth(2, 500)

  def reloadFile(self):
    if self.logfile is not None:
      self.openFile(self.logfile_name)

  def openFile(self, filename=None):
    if filename is None:
      filename=QFileDialog.getOpenFileName(self, caption=u'Select logfile')
    self.showLog(Logfile(filename))
    self.logfile_name=filename

  def showLog(self, logfile):
    '''
    Display the Logfile object in the ui treeview.
    
    :param Logfile logfile: An Logfile instance to be displayed.
    '''
    self.logfile=None
    for ignore in range(self.ui.filterThread.count()-1):
      self.ui.filterThread.removeItem(-1)

    threads=[]
    for entry in logfile.entries:
      if entry.thread and entry.thread not in threads:
        threads.append(entry.thread)
    threads.sort()
    if threads:
      self.ui.filterThread.show()
      self.ui.filterThreadLabel.show()
      map(self.ui.filterThread.addItem, threads)
    else:
      self.ui.filterThread.hide()
      self.ui.filterThreadLabel.hide()

    self.logfile=logfile
    self.updateLog()
    self.logfile.entriesUpdated.connect(self.updateLog)

  def updateLog(self, from_idx=None, to_idx=None):
    if self.logfile is None:
      return

    if from_idx is None or to_idx is None:
      self.ui.logTree.clear()
      entries=self.logfile.entries
    else:
      entries=self.logfile.entries[from_idx:to_idx+1]
    minseverity=str(self.ui.minSeverity.currentText())
    minid=eval('logging.'+minseverity)
    showthread=str(self.ui.filterThread.currentText())

    for entry in entries:
      if entry.severity<minid:
        continue
      if showthread!='All' and entry.thread!=showthread:
        continue
      if entry.thread:
        ctxt=entry.thread+u': '+entry.comment_info
      else:
        ctxt=entry.comment_info
      root=TreeWidgetTimeItem([entry.sseverity, entry.time, ctxt,
                            entry.source_file, str(entry.source_line), entry.source_method], 1)
      if entry.severity>=logging.ERROR:
        root.setTextColor(0, QColor(255, 0, 0))
      elif entry.severity>=logging.WARN:
        root.setTextColor(0, QColor(150, 150, 0))
      elif entry.severity<logging.INFO:
        root.setTextColor(0, QColor(100, 100, 100))

      self.ui.logTree.addTopLevelItem(root)
      if entry.comment_text:
        QTreeWidgetItem(root, ['', '', entry.comment_text, ''])

    self.ui.logTree.resizeColumnToContents(0)
    self.ui.logTree.resizeColumnToContents(1)
    self.ui.logTree.resizeColumnToContents(3)
    self.ui.logTree.resizeColumnToContents(4)
    if self.ui.follow.isChecked():
      self.ui.logTree.scrollToBottom()
