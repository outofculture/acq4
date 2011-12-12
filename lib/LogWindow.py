import time
import traceback
import sys

from PyQt4 import QtGui, QtCore
import LogWidgetTemplate
from FeedbackButton import FeedbackButton
import configfile
from DataManager import DirHandle
from HelpfulException import HelpfulException
from Mutex import Mutex
import numpy as np
from pyqtgraph.FileDialog import FileDialog
from debug import printExc
import weakref
import re

#from lib.Manager import getManager

#WIN = None

class LogButton(FeedbackButton):

    def __init__(self, *args):
        FeedbackButton.__init__(self, *args)
        #self.setMaximumHeight(30)
        global WIN
        self.clicked.connect(WIN.show)
        WIN.buttons.append(weakref.ref(self))
    
    #def close(self):
        #global WIN
        #WIN.buttons.remove(self)

class LogWindow(QtGui.QMainWindow):
    

    """LogWindow contains a LogWidget inside a window. LogWindow is responsible for collecting messages generated by the program/user, formatting them into a nested dictionary,
    and saving them in a log.txt file. The LogWidget takes care of displaying messages.
    
    Messages can be logged by calling logMsg or logExc functions from lib.Manager. These functions call the LogWindow.logMsg and LogWindow.logExc functions, but other classes 
    should not call the LogWindow functions directly.
    
    """

    
    def __init__(self, manager):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("Log")
        self.wid = LogWidget(self, manager)
        self.wid.ui.input = QtGui.QLineEdit()
        self.wid.ui.gridLayout.addWidget(self.wid.ui.input, 2, 0, 1, 3)
        self.wid.ui.dirLabel.setText("Current Storage Directory: None")
        self.setCentralWidget(self.wid)
        self.resize(1000, 500)
        self.manager = manager
        #global WIN
        WIN = self
        global WIN
        self.msgCount = 0
        self.logCount=0
        self.logFile = None
        configfile.writeConfigFile('', self.fileName())  ## start a new temp log file, destroying anything left over from the last session.
        self.buttons = [] ## weak references to all Log Buttons get added to this list, so it's easy to make them all do things, like flash red.
        self.lock = Mutex()
        

        ## self.wid.ui.input is a QLineEdit
        ## self.wid.ui.output is a QPlainTextEdit
        
        self.wid.ui.input.returnPressed.connect(self.textEntered)
        
        #self.sigDisplayEntry.connect(self.displayEntry)
        
        
    def logMsg(self, msg, importance=5, msgType='status', **kwargs):
        """msg: the text of the log message
           msgTypes: user, status, error, warning (status is default)
           importance: 0-9 (0 is low importance, 9 is high, 5 is default)
           other keywords:
              exception: a tuple (type, exception, traceback) as returned by sys.exc_info()
              docs: a list of strings where documentation related to the message can be found
              reasons: a list of reasons (as strings) for the message
              traceback: a list of formatted callstack/trackback objects (formatting a traceback/callstack returns a list of strings), usually looks like [['line 1', 'line 2', 'line3'], ['line1', 'line2']]
           Feel free to add your own keyword arguments. These will be saved in the log.txt file, but will not affect the content or way that messages are displayed.
        """

        
        try:
            currentDir = self.manager.getCurrentDir()
        except:
            currentDir = None
        if isinstance(currentDir, DirHandle):
            kwargs['currentDir'] = currentDir.name()
        else:
            kwargs['currentDir'] = None
        
        now = str(time.strftime('%Y.%m.%d %H:%M:%S'))
        name = 'LogEntry_' + str(self.msgCount)
        self.msgCount += 1
        entry = {
            #'docs': None,
            #'reasons': None,
            'message': msg,
            'timestamp': now,
            'importance': importance,
            'msgType': msgType,
            #'exception': exception,
        }
        for k in kwargs:
            entry[k] = kwargs[k]
            
        self.processEntry(entry)
        
        ## Copy in information from the exception if it happens to be there
        if entry.get('exception', None) is not None and 'msgType' in entry['exception']:
            entry['msgType'] = entry['exception']['msgType']
        
        self.saveEntry({name:entry})
        self.wid.addEntry(entry) ## takes care of displaying the entry if it passes the current filters on the logWidget
        #self.wid.displayEntry(entry)
        
        if entry['msgType'] == 'error':
            self.flashButtons()
        
        
    def logExc(self, *args, **kwargs):
        """Calls logMsg, but adds in the current exception and callstack. Must be called within an except block, and should only be called if the exception is not re-raised. Unhandled exceptions, or exceptions that reach the top of the callstack are automatically logged, so logging an exception that will be re-raised can cause the exception to be logged twice. Takes the same arguments as logMsg."""
        kwargs['exception'] = sys.exc_info()
        kwargs['traceback'] = [['Callstack: \n'] + traceback.format_stack()[:-3] + ["------- exception caught ----------"]]
        self.logMsg(*args, **kwargs)
        
    def processEntry(self, entry):
        ## pre-processing common to saveEntry and displayEntry

        if entry.get('exception', None) is not None:
            exc_info = entry.pop('exception')
            entry['exception'] = self.exceptionToDict(*exc_info)
        else:
            entry['exception'] = None

        
    def textEntered(self):
        msg = str(self.wid.ui.input.text())
        try:
            currentDir = self.manager.getCurrentDir()
        except:
            currentDir = None
        self.logMsg(msg, importance=8, msgType='user', currentDir=currentDir)
        self.wid.ui.input.clear()

    
    def exceptionToDict(self, exType, exc, tb):
        #lines = (traceback.format_stack()[:-skip] 
            #+ ["  ---- exception caught ---->\n"] 
            #+ traceback.format_tb(sys.exc_info()[2])
            #+ traceback.format_exception_only(*sys.exc_info()[:2]))
        
        excDict = {}
        excDict['message'] = traceback.format_exception(exType, exc, tb)[-1]
        excDict['traceback'] = traceback.format_exception(exType, exc, tb)[:-1]
        if hasattr(exc, 'docs'):
            if len(exc.docs) > 0:
                excDict['docs'] = exc.docs
        if hasattr(exc, 'reasons'):
            if len(exc.reasons) > 0:
                excDict['reasons'] = exc.reasons
        if hasattr(exc, 'kwargs'):
            for k in exc.kwargs:
                excDict[k] = exc.kwargs[k]
        if hasattr(exc, 'oldExc'):
            excDict['oldExc'] = self.exceptionToDict(*exc.oldExc)
        return excDict
        
    def flashButtons(self):
        for b in self.buttons:
            if b() is not None:
                b().failure(tip='An error occurred. Please see the log.', limitedTime = False)
            
    def resetButtons(self):
        for b in self.buttons:
            if b() is not None:
                b().reset()
            #try:
                #b.reset()
            #except RuntimeError:
                #self.buttons.remove(b)
                #print "Removed a logButton from logWindow's list. button:", b
            
        
    def makeError1(self):
        try:
            self.makeError2()
            #print x
        except:
            t, exc, tb = sys.exc_info()
            #logExc(message="This button doesn't work", reasons='reason a, reason b', docs='documentation')
            #if isinstance(exc, HelpfulException):
                #exc.prependErr("Button doesn't work", (t,exc,tb), reasons = ["It's supposed to raise an error for testing purposes", "You're doing it wrong."])
                #raise
            #else:
            raise HelpfulException(message='This button does not work.', exc=(t, exc, tb), reasons=["It's supposed to raise an error for testing purposes", "You're doing it wrong."])
    
    def makeError2(self):
        try:
            print y
        except:
            t, exc, tb = sys.exc_info()
            raise HelpfulException(message='msg from makeError', exc=(t, exc, tb), reasons=["reason one", "reason 2"], docs=['what, you expect documentation?'])
            
    def show(self):
        QtGui.QMainWindow.show(self)
        self.activateWindow()
        self.raise_()
        self.resetButtons()
        
    def fileName(self):
        ## return the log file currently used
        if self.logFile is None:
            return "tempLog.txt"
        else:
            return self.logFile.name()
        
    def setLogDir(self, dh):
        if self.fileName() == dh.name():
            return
        
        oldfName = self.fileName()
        if self.logFile is not None:
            self.logMsg('Moving log storage to %s.' % (self.logFile.name(relativeTo=self.manager.baseDir))) ## make this note before we change the log file, so when a log ends, you know where it went after.
        
        self.logMsg('Moving log storage to %s.' % (dh.name(relativeTo=self.manager.baseDir))) ## make this note before we change the log file, so when a log ends, you know where it went after.
        
        if oldfName == 'tempLog.txt':
            with self.lock:
                temp = configfile.readConfigFile(oldfName)
        else:
            temp = {}
                
        if dh.exists('log.txt'):
            self.logFile = dh['log.txt']
            with self.lock:
                self.msgCount = len(configfile.readConfigFile(self.logFile.name()))
            newTemp = {}
            for v in temp.values():
                self.msgCount += 1
                newTemp['LogEntry_'+str(self.msgCount)] = v
            self.saveEntry(newTemp)
        else:
            self.logFile = dh.createFile('log.txt')
            self.saveEntry(temp)
        
        self.logMsg('Moved log storage from %s to %s.' % (oldfName, self.fileName()))
        self.wid.ui.dirLabel.setText("Current Storage Directory: " + self.fileName())
        self.manager.sigLogDirChanged.emit(dh)
        
    def getLogDir(self):
        if self.logFile is None:
            return None
        else:
            return self.logFile.parent()
        
    def saveEntry(self, entry):  
        with self.lock:
            configfile.appendConfigFile(entry, self.fileName())
            

class LogWidget(QtGui.QWidget):
    
    sigDisplayEntry = QtCore.Signal(object) ## for thread-safetyness
    
    def __init__(self, parent, manager):
        QtGui.QWidget.__init__(self, parent)
        self.ui = LogWidgetTemplate.Ui_Form()
        self.manager = manager
        self.ui.setupUi(self)
        #self.ui.input.hide()
        self.ui.filterTree.topLevelItem(1).setExpanded(True)
        
        self.entries = [] ## stores all log entries in memory
        self.cache = {} ## for storing html strings of entries that have already been processed
        #self.currentEntries = None ## recordArray that stores currently displayed entries -- so that if filters get more restrictive we can just refilter this list instead of filtering everything
        self.typeFilters = []
        self.importanceFilter = 0
        self.dirFilter = False
        self.entryArray = np.zeros(0, dtype=[ ### a record array for quick filtering of entries
            ('index', 'int32'),
            ('importance', 'int32'),
            ('msgType', '|S10'),
            ('directory', '|S100')
        ])
        
        self.filtersChanged()
        
        self.sigDisplayEntry.connect(self.displayEntry)
        self.ui.exportHtmlBtn.clicked.connect(self.exportHtml)
        self.ui.filterTree.itemChanged.connect(self.setCheckStates)
        self.ui.importanceSlider.valueChanged.connect(self.filtersChanged)
        
        
    def loadFile(self, f):
        """Load the file, f. f must be able to be read by configfile.py"""
        log = configfile.readConfigFile(f)
        self.entries = []
        self.entryArray = np.zeros(len(log),dtype=[
            ('index', 'int32'),
            ('importance', 'int32'),
            ('msgType', '|S10'),
            ('directory', '|S100')
        ])
                                   
        i = 0
        for v in log.itervalues():
            self.entries.append(v)
            self.entryArray[i] = np.array([(i, v.get('importance', 5), v.get('msgType', 'status'), v.get('currentDir', ''))], dtype=[('index', 'int32'), ('importance', 'int32'), ('msgType', '|S10'), ('directory', '|S100')])
            i += 1
            
        self.filterEntries() ## puts all entries through current filters and displays the ones that pass
        
    def addEntry(self, entry):
        self.entries.append(entry)
        i = len(self.entryArray)
        
        entryDir = entry.get('currentDir', None)
        if entryDir is None:
            entryDir = ''
            
        arr = np.array([(i, entry['importance'], entry['msgType'], entryDir)], dtype = [('index', 'int32'), ('importance', 'int32'), ('msgType', '|S10'), ('directory', '|S100')])
        self.entryArray.resize(i+1)
        #self.entryArray[i] = [(i, entry['importance'], entry['msgType'], entry['currentDir'])]
        self.entryArray[i] = arr
        self.checkDisplay(entry) ## displays the entry if it passes the current filters
        #np.append(self.entryArray, np.array(i, [[i, entry['importance'], entry['msgType'], entry['currentDir']]]), dtype = [('index', int), ('importance', int), ('msgType', str), ('directory', str)])
    
    def setCheckStates(self, item, column):
        if item == self.ui.filterTree.topLevelItem(1):
            if item.checkState(0):
                for i in range(item.childCount()):
                    item.child(i).setCheckState(0, QtCore.Qt.Checked)
        elif item.parent() == self.ui.filterTree.topLevelItem(1):
            if not item.checkState(0):
                self.ui.filterTree.topLevelItem(1).setCheckState(0, QtCore.Qt.Unchecked)
        self.filtersChanged()
        
    def filtersChanged(self):
        ### Update self.typeFilters, self.importanceFilter, and self.dirFilter to reflect changes.
        tree = self.ui.filterTree
        
        self.typeFilters = []
        for i in range(tree.topLevelItem(1).childCount()):
            child = tree.topLevelItem(1).child(i)
            if tree.topLevelItem(1).checkState(0) or child.checkState(0):
                text = child.text(0)
                self.typeFilters.append(str(text))
            
        self.importanceFilter = self.ui.importanceSlider.value()
    
        self.updateDirFilter()
            #self.dirFilter = self.manager.getDirOfSelectedFile().name()
        #else:
            #self.dirFilter = False
            
        self.filterEntries()
        
    def updateDirFilter(self, dh=None):
        if self.ui.filterTree.topLevelItem(0).checkState(0):
            if dh==None:
                self.dirFilter = self.manager.getDirOfSelectedFile().name()
            else:
                self.dirFilter = dh.name()
        else:
            self.dirFilter = False
        
    
        
    def filterEntries(self):
        """Runs each entry in self.entries through the filters and displays if it makes it through."""
        ### make self.entries a record array, then filtering will be much faster (to OR true/false arrays, + them)
        typeMask = self.entryArray['msgType'] == ''
        for t in self.typeFilters:
            typeMask += self.entryArray['msgType'] == t
        mask = (self.entryArray['importance'] > self.importanceFilter) * typeMask
        if self.dirFilter != False:
            d = np.ascontiguousarray(self.entryArray['directory'])
            j = len(self.dirFilter)
            i = len(d)
            d = d.view(np.byte).reshape(i, 100)[:, :j]
            d = d.reshape(i*j).view('|S%s' %str(j))
            mask *= (d == self.dirFilter)
            
            
        self.ui.output.clear()
        indices = list(self.entryArray[mask]['index'])
        inds = indices
        
        #if self.dirFilter != False:
            #j = len(self.dirFilter)
            #for i, n in inds:
                #if not self.entries[n]['currentDir'][:j] == self.dirFilter:
                    #indices.pop(i)
                    
        self.displayEntry([self.entries[i] for i in indices])
                          
    def checkDisplay(self, entry):
        ### checks whether entry passes the current filters and displays it if it does.
        if entry['msgType'] not in self.typeFilters:
            return
        elif entry['importance'] < self.importanceFilter:
            return
        elif self.dirFilter is not False:
            if entry['currentDir'][:len(self.dirFilter)] != self.dirFilter:
                return
        else:
            self.displayEntry([entry])
    
        
    def displayEntry(self, entries):
        ## entries should be a list of log entries
        
        ## for thread-safetyness:
        isGuiThread = QtCore.QThread.currentThread() == QtCore.QCoreApplication.instance().thread()
        if not isGuiThread:
            self.sigDisplayEntry.emit(entries)
            return
        
        else:
            for entry in entries:
                if not self.cache.has_key(id(entry)):
                    self.cache[id(entry)] = []
                    ## determine message color:
                    if entry['msgType'] == 'status':
                        color = 'green'
                    elif entry['msgType'] == 'user':
                        color = 'blue'
                    elif entry['msgType'] == 'error':
                        color = 'red'
                    elif entry['msgType'] == 'warning':
                        color = '#DD4400' ## orange
                    else:
                        color = 'black'
                        
                  
                    
                        
                    if entry.has_key('exception') or entry.has_key('docs') or entry.has_key('reasons'):
                        self.displayComplexMessage(entry, color)
                    else: 
                        self.displayText(entry['message'], entry, color, timeStamp=entry['timestamp'])
                    for x in self.cache[id(entry)]:
                        self.ui.output.appendHtml(x)
                else:
                    for x in self.cache[id(entry)]:
                        self.ui.output.appendHtml(x)
                        
    def cleanText(self, text):
        text = re.sub(r'&', '&amp;', text)
        text = re.sub(r'>','&gt;', text)
        text = re.sub(r'<', '&lt;', text)
        return text
                    
    def displayComplexMessage(self, entry, color='black'):
        self.displayText(entry['message'], entry, color, timeStamp = entry['timestamp'], clean=True)
        if entry.has_key('reasons'):
            reasons = self.formatReasonStrForHTML(entry['reasons'])
            self.displayText(reasons, entry, 'black', clean=False)
        if entry.has_key('docs'):
            docs = self.formatDocsStrForHTML(entry['docs'])
            self.displayText(docs, entry, 'black', clean=False)
        if entry.get('exception', None) is not None:
            self.displayException(entry['exception'], entry, 'black', tracebacks=entry.get('traceback', None))
            

    
    def displayException(self, exception, entry, color, count=None, tracebacks=None):
        ### Here, exception is a dict that holds the message, reasons, docs, traceback and oldExceptions (which are also dicts, with the same entries)
        ## the count and tracebacks keywords are for calling recursively
        
        if count is None:
            count = 1
        else:
            count += 1
        
        if tracebacks is None:
            tracebacks = []
            
        indent = 10
        
        text = self.cleanText(exception['message'])
        if exception.has_key('oldExc'):  
            self.displayText("&nbsp;"*indent + str(count)+'. ' + text, entry, color, clean=False)
        else:
            self.displayText("&nbsp;"*indent + str(count)+'. Original error: ' + text, entry, color, clean=False)
            
        tracebacks.append(exception['traceback'])
        
        if exception.has_key('reasons'):
            reasons = self.formatReasonsStrForHTML(exception['reasons'])
            self.displayText(reasons, entry, color, clean=False)
        if exception.has_key('docs'):
            docs = self.formatDocsStrForHTML(exception['docs'])
            self.displayText(docs, entry, color, clean=False)
        
        if exception.has_key('oldExc'):
            self.displayException(exception['oldExc'], entry, color, count=count, tracebacks=tracebacks)
        else:
            if len(tracebacks)==count+1:
                n=0
            else: 
                n=1
            for i, tb in enumerate(tracebacks):
                self.displayTraceback(tb, entry, number=i+n)
        
        
    def displayText(self, msg, entry, colorStr='black', timeStamp=None, clean=True):
        if clean:
            msg = self.cleanText(msg)
        
        if msg[-1:] == '\n':
            msg = msg[:-1]     
        msg = '<br />'.join(msg.split('\n'))
        if timeStamp is not None:
            strn = '<b style="color:black"> %s </b> <span style="color:%s"> %s </span>' % (timeStamp, colorStr, msg) 
        else:
            strn = '<span style="color:%s"> %s </span>' % (colorStr, msg)
        #self.ui.output.appendHtml(strn)
        self.cache[id(entry)].append(strn)
            
    def displayTraceback(self, tb, entry, color='grey', number=1):
        tb = [self.cleanText(x) for x in tb]
        lines = []
        indent = 16
        prefix = ''
        for l in ''.join(tb).split('\n'):
            if l == '':
                continue
            if l[:9] == "Traceback":
                prefix = ' ' + str(number) + '. '
                continue
            spaceCount = 0
            while l[spaceCount] == ' ':
                spaceCount += 1
            if prefix is not '':
                spaceCount -= 1
            lines.append("&nbsp;"*(indent+spaceCount*4) + prefix + l)
            prefix = ''
        self.displayText('<br />'.join(lines), entry, color, clean=False)
        
    def formatReasonsStrForHTML(self, reasons):
        indent = 6
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
        reasonStr = "&nbsp;"*16 + "Possible reasons include: <br>"
        for i, r in enumerate(reasons):
            r = self.cleanText(r)
            reasonStr += "&nbsp;"*22 + letters[i] + ". " + r + "<br>"
        return reasonStr[:-4]
    
    def formatDocsStrForHTML(self, docs):
        indent = 6
        docStr = "&nbsp;"*16 + "Relevant documentation: <br>"
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
        for i, d in enumerate(docs):
            d = self.cleanText(d)
            docStr += "&nbsp;"*22 + letters[i] + ". " + d + "<br>"
        return docStr[:-4]
    
    def exportHtml(self, fileName=False):
        if fileName is False:
            self.fileDialog = FileDialog(self, "Save HTML as...", self.manager.getCurrentDir().name())
            #self.fileDialog.setFileMode(QtGui.QFileDialog.AnyFile)
            self.fileDialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
            self.fileDialog.show()
            self.fileDialog.fileSelected.connect(self.exportHtml)
            return
        if fileName[-5:] != '.html':
            fileName += '.html'
        doc = self.ui.output.document().toHtml('utf-8')
        f = open(fileName, 'w')
        f.write(doc.encode('utf-8'))
        f.close()
        
        
    
    def makeError1(self):
        ### just for testing error logging
        try:
            self.makeError2()
            #print x
        except:
            t, exc, tb = sys.exc_info()
            #logExc(message="This button doesn't work", reasons='reason a, reason b', docs='documentation')
            #if isinstance(exc, HelpfulException):
                #exc.prependErr("Button doesn't work", (t,exc,tb), reasons = ["It's supposed to raise an error for testing purposes", "You're doing it wrong."])
                #raise
            #else:
            printExc("This is the message sent to printExc.")
            #raise HelpfulException(message='This button does not work.', exc=(t, exc, tb), reasons=["It's supposed to raise an error for testing purposes", "You're doing it wrong."])
    
    def makeError2(self):
        ### just for testing error logging
        try:
            print y
        except:
            t, exc, tb = sys.exc_info()
            raise HelpfulException(message='msg from makeError', exc=(t, exc, tb), reasons=["reason one", "reason 2"], docs=['what, you expect documentation?'])

        
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication([])
    log = LogWindow()
    log.show()
    original_excepthook = sys.excepthook
    
    def excepthook(*args):
        global original_excepthook
        log.displayException(*args)
        ret = original_excepthook(*args)
        sys.last_traceback = None           ## the important bit
        
    
    sys.excepthook = excepthook

    app.exec_()