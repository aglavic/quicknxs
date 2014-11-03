from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as Navigationtoolbar
from matplotlib.figure import Figure

class MplCanvas(FigureCanvas):
    
    def __init__(self):
        
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        
        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
class logNavigationtoolbar(Navigationtoolbar):
    
    logtog = QtCore.pyqtSignal(bool)
    
    def __init__(self, canvas, parent):
        
        Navigationtoolbar.__init__(self, canvas, parent)
        self.clearButtons = []
        
        # search through existing buttons
        # next use for placement of custom button
        next = None
        for c in self.findChildren(QtGui.QToolButton):
            if next is None:
                next = c
                
            # don't want to see subplots and customize
            if str(c.text()) in ('Subplots','Customize'):
                c.defaultAction().setVisible(False)
                continue
        
            # need to keep track of pan and zoom buttons
            if str(c.text()) in ('Pan','Zoom'):
                self.clearButtons.append(c)
                next = None
                
        icon=QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/MPL Toolbar/toggle-xlog.png"), 
                       QtGui.QIcon.Normal, 
                       QtGui.QIcon.Off)
        picker = QtGui.QAction("Pick", self)
        picker.setIcon(icon)
        picker.setCheckable(True)
        picker.setToolTip("Toggle x-logarithmic scale")
        self.picker = picker
        button = QtGui.QToolButton(self)
        button.setDefaultAction(self.picker)
        
        # add it to the toolbar, and connect event
        self.insertWidget(next.defaultAction(), button)
        picker.toggled.connect(self.logtoggle)
        
    def logtoggle(self, checked):
        self.logtog.emit(checked)
        
class logMatplotlibWidget(QtGui.QWidget):
    
    def __init__(self, parent=None):
        
        QtGui.QWidget.__init__(self, parent)
        self.create_frametoolbar()
        
    def create_frametoolbar(self):
        
        self.frame = QtGui.QWidget()
        self.canvas = MplCanvas()
        self.canvas.setParent(self.frame)
        self.mpltoolbar = logNavigationtoolbar(self.canvas, self.frame)
        
        self.vbl = QtGui.QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.vbl.addWidget(self.mpltoolbar)
        self.setLayout(self.vbl)
        
        
        