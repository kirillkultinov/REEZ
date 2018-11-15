import sys
import platform
#import pygraphviz
import PyQt4
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import QtGui, QtCore
from BinaryProcessor import BinaryProcessor
from networkx.drawing import nx_agraph
from qdot import *
from graphviz import Source
import time

global binaryProcessor
global codeView
callGraphString = None
A = None
G = None
__version__ = "0.0.1"

class DisassemblyWidget(QtGui.QGraphicsView):
    def __init__(self, parent=None):
        QtGui.QGraphicsView.__init__(self)
        self.groupBox = QtGui.QGroupBox('Assembly Viewer')
        self.textForm = QtGui.QFormLayout()
        self.scrollView = QtGui.QScrollArea(self)
        self.disassemblyView = QtGui.QLabel()
        self.disassemblyView.setText("")

        self.textForm.addRow(self.disassemblyView)
        self.groupBox.setLayout(self.textForm)
        self.scrollView.setWidget(self.groupBox)
        self.scrollView.setWidgetResizable(True)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.scrollView)

        self.font = QtGui.QFont("Arial", 8)
        self.disassemblyView.setFont(self.font)

    def setFontSize(self, fontSize):
        self.font.setPointSize(fontSize)
        self.disassemblyView.setFont(self.font)

    def setDisassemblyText(self, text):
        self.disassemblyView.setText(str(text))


class CallGraphWidget(QtGui.QGraphicsView):
    
    graph = None

    def __init__(self, parent=None):
        QtGui.QGraphicsView.__init__(self)
        self._scene = QtGui.QGraphicsScene(self)
        self._scene.setSceneRect(QtCore.QRectF(0, 0, 200, 300))
        self.setScene(self._scene)
        
        #self._scene.addText("Hello, world!");

        self.setDragMode(self.ScrollHandDrag)
        self.setTransformationAnchor(self.AnchorUnderMouse)

        self.x, self.y = 0.0, 0.0
        #self.zoom_ratio = 1.0
        self.zoom_to_fit_on_resize = False
        self.animation = NoAnimation(self)
        self.presstime = None
        self.highlight = None

    def mouseDoubleClickEvent(self, event):
        startTime = time.time()
        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            xPos = pos.x()
            yPos = pos.y()
            nodes = self.parser.getNodes()
            textShapes = []
            for node in nodes:
                shapes = node.getShapes()
                for shape in shapes:
                    if isinstance(shape, TextShape):
                        textShapes.append(shape)
            
            
            count = 0
            disassembly = ""
            for text in textShapes:
                xMiddle = text.getXCoord()
                width = text.getWidth()
                xUpper = xMiddle + width/2
                xLower = xMiddle - width/2
                y = text.getYCoord()
                yLower = y - 10
                yUpper = y + 10
                if(xPos <= xUpper and xPos >= xLower and yPos <= yUpper and yPos >= yLower ):
                    funcName = text.getText()
                    #print("clicked " + funcName)
                    disassembly = binaryProcessor.disassembleFunction(str(funcName))
                    #print("result: " + disassembly)
                    if disassembly == "":
                        disassembly = "There is nothing for " + funcName
                    codeView.setDisassemblyText(disassembly)
                    print("time taken to display disassembly: ---- %s seconds ----" % (time.time() - startTime))
                    break
                count = count + 1
                
            


    def set_dotcode(self, dotcode, filename='<stdin>'):
        if isinstance(dotcode, unicode):
            dotcode = dotcode.encode('utf8')
        p = subprocess.Popen(
            [self.filter, '-Txdot'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            universal_newlines=True
        )
        xdotcode, error = p.communicate(dotcode)
        if p.returncode != 0:
            mbox = QtGui.QMessageBox()
            mbox.setWindowTitle('QDot Viewer')
            mbox.setText('Error: ' + error)
            mbox.exec_()
            return False
        try:
            self.set_xdotcode(xdotcode)
        except ParseError, ex:
            mbox = QtGui.QMessageBox(self)
            mbox.setWindowTitle('QDot Viewer')
            mbox.setText('Error: ' + str(ex))
            mbox.exec_()
            return False
        else:
            self.openfilename = filename
            return True

    def set_xdotcode(self, xdotcode):
        self.parser = XDotParser(xdotcode)
        self.graph = self.parser.parse()
        (w, h) = self.graph.get_size()
        self._scene = QtGui.QGraphicsScene(self)
        self._scene.setSceneRect(QtCore.QRectF(0, 0, w, h))
        self.setScene(self._scene)

        #self.resize(w, h)

        #self.zoom_image(self.zoom_ratio, center=True)

    def zoom_image(self, zoom_ratio, center=False, pos=None):
        self.scale(zoom_ratio, zoom_ratio)

    def zoom_to_area(self, x1, y1, x2, y2):
        self.fitInView(QtCore.QRectF(x1, y1, x2, y2), QtCore.Qt.KeepAspectRatio)

    def zoom_to_fit(self):
        rectf = self._scene.sceneRect()
        self.fitInView(rectf, QtCore.Qt.KeepAspectRatio)

    def zoom_cancel(self):
        self.resetTransform()
        #self.zoom_ratio = 1.0

    def set_filter(self, filter):
        self.filter = filter

    def drawForeground(self, painter, rect):
        if self.graph:
            self.graph.draw(self._scene, painter, rect)

    def wheelEvent(self, event):
        if event.delta() > 0:
            self.zoom_image(1.0 + 1.0 / 3)
        else:
            self.zoom_image(3.0 / 4)


class ViewsWidget(QtGui.QWidget):
    
    def __init__(self, parent):
        super(ViewsWidget, self).__init__(parent)
        hbox = QtGui.QHBoxLayout(self)
        self.qdotWidget = CallGraphWidget(self) #call graph holder
        global codeView
        codeView = DisassemblyWidget(self) # disassembly holder
        #right.setFrameShape(QtGui.QFrame.StyledPanel)
        #create splitter
        splitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        #add right and left widgets
        splitter.addWidget(self.qdotWidget)
        splitter.addWidget(codeView)
        #set stratch factor
        splitter.setStretchFactor(1, 1)
        #adjust the UI
        width = int(parent.frameGeometry().width()) / 2
        splitter.setSizes([width, 150])
        
        hbox.addWidget(splitter)
        self.setLayout(hbox)
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
        #self.setGeometry(300, 300, 300, 200)
        self.showMaximized()

class Terminal(QtGui.QWidget):
    def __init__(self, parent):
        super(Terminal, self).__init__(parent)
        self.resize(300, 500)
        self.process = QProcess(self)
        self.term = QWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.term)
        self.process.start('xterm')

class ApplicationUI(QtGui.QMainWindow):
    

    def __init__(self):
        super(ApplicationUI, self).__init__()
        self.initUI()
    
    def initUI(self):
        #create menu
        self.createToolBars()

        self.createMenu()

        self.setWindowTitle('Project')

        self.fileName = ""
        self.callGraph = ""
        self.initialized  = False

        self.showMaximized()

    def createToolBars(self):
        #add exit icon
        exitAction = QtGui.QAction(QtGui.QIcon('res/exit.png'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.close)
        #add import file icon
        importAction = QtGui.QAction(QtGui.QIcon('res/import.png'), 'Load Binary', self)
        importAction.setShortcut('Ctrl+O')
        importAction.triggered.connect(self.showFileDialog)
        #add export file icon
        exportAction = QtGui.QAction(QtGui.QIcon('res/export.png'), 'Save Graph to a file', self)
        exportAction.setShortcut('Ctrl+E')
        exportAction.triggered.connect(self.exportGraph)
        #add tool bars
        self.toolBarMain = self.addToolBar("")
        self.addToolBarBreak()
        
        #add elements to the main toolbar
        self.toolBarMain.addAction(exitAction)
        self.toolBarMain.addAction(importAction)
        self.toolBarMain.addAction(exportAction)

    def exportGraph(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, 'Save File', '', filter='.pdf')
        if fileName != "":
            if str(fileName).find(".pdf") == -1:
                fileName = fileName + ".gv"
            if self.callGraph != "":
                src = Source(self.callGraph)
                #fileName = fileName[1:]
                src.render(str(fileName))

    def _onZoomIn(self):
        self.viewsWidget.qdotWidget.zoom_image(1.0 + 1.0 / 3)

    def _onZoomOut(self):
        self.viewsWidget.qdotWidget.zoom_image(3.0 / 4)

    def _onZoomFit(self):
        self.viewsWidget.qdotWidget.zoom_to_fit()

    def _onZoom100(self):
        self.viewsWidget.qdotWidget.zoom_cancel()

    def createMenu(self):
        self.menuToolBar = self.menuBar()
        #quit sub menu
        quitAction = QtGui.QAction("exit", self)
        quitAction.setStatusTip('Exit the app')
        quitAction.setShortcut('Ctrl+Q')
        quitAction.triggered.connect(self.close)
        #select file sub menu
        selectFile = QtGui.QAction("Load binary", self)
        selectFile.setStatusTip("Load new binary file")
        selectFile.setShortcut('Ctrl+O')
        selectFile.triggered.connect(self.showFileDialog)
        #add menu options to file tab
        fileMenu = self.menuToolBar.addMenu('&File')
        fileMenu.addAction(selectFile)
        fileMenu.addAction(quitAction)

    def showFileDialog(self):
        self.fileName = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
        '/home')
        if(self.fileName != ""):
            startTime = time.time()
            self.processFile(self.fileName)
            print("time taken to visualize graph: ---- %s seconds ----" % (time.time() - startTime))
        """self.dialog = QtGui.QFileDialog()
        self.dialog.setFilter(QtCore.QDir.Executable | QtCore.QDir.Files | QtCore.QDir.AllDirs)
        self.dialog.setDirectory('/home')
        self.dialog.setWindowTitle('Open File')
        if self.dialog.exec_() == QtGui.QDialog.Accepted:
            self.fileName = self.dialog.selectedFiles()[0]
            print("file name " + self.fileName)
            if(self.fileName != ""):
                self.processFile(self.fileName)"""


    def processFile(self, fileName):
        #set up views for the call graph and disassembly
        self.viewsWidget = ViewsWidget(self)
        self.setCentralWidget(self.viewsWidget)
        self.set_filter(self.filter)
        if self.initialized == False:
            #set up tool bar for the graph
            self.graphToolbar = self.addToolBar("")
            #icons for graph toolbar
            _zoomInAct = QtGui.QAction(
                QtGui.QIcon.fromTheme('zoom-in'), 'Zoom In', self)
            _zoomInAct.triggered.connect(self._onZoomIn)
            _zoomOutAct = QtGui.QAction(
                QtGui.QIcon.fromTheme('zoom-out'), 'Zoom Out', self)
            _zoomOutAct.triggered.connect(self._onZoomOut)
            _zoomFitAct = QtGui.QAction(
                QtGui.QIcon.fromTheme('zoom-fit-best'), 'Zoom Fit', self)
            _zoomFitAct.triggered.connect(self._onZoomFit)
            _zoom100Act = QtGui.QAction(
                QtGui.QIcon.fromTheme('zoom-original'), 'Zoom 100%', self)
            _zoom100Act.triggered.connect(self._onZoom100)
            self.graphToolbar.addAction(_zoomInAct)
            self.graphToolbar.addAction(_zoomOutAct)
            self.graphToolbar.addAction(_zoomFitAct)
            self.graphToolbar.addAction(_zoom100Act)
            self.hint = QtGui.QLabel()
            self.hint.setText("font size:")
            self.graphToolbar.addWidget(self.hint)
            self.cb = QComboBox()
            self.cb.addItems(["8", "9", "10", "11", "12", "13", "14", "15"])
            self.cb.currentIndexChanged.connect(self.selectionChange)
            self.graphToolbar.addWidget(self.cb)
            #add terminal option to the main toolbar
            termAction = QtGui.QAction(QtGui.QIcon('res/terminal.png'), 'terminal', self)
            termAction.setShortcut('Ctrl+T')
            termAction.triggered.connect(self.showTerminal)
            self.toolBarMain.addAction(termAction)
            self.initialized = True
        #process binary
        global binaryProcessor
        binaryProcessor = BinaryProcessor(fileName)
        self.callGraph = binaryProcessor.getCallGraph()
        if self.viewsWidget.qdotWidget.set_dotcode(self.callGraph, '<stdin>'):
            print("")

    def showTerminal(self):
        self.term = Terminal(self)
        self.term.show()

    def selectionChange(self, i):
        codeView.setFontSize(int(self.cb.currentText()))
            
    def setFilter(self, filter):
        self.filter = filter        

    def set_filter(self, filter):
        self.viewsWidget.qdotWidget.set_filter(filter)

    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, 'Message',
        "Are you sure you want to quit?", QtGui.QMessageBox.Yes | 
        QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    import optparse
    #print("hello")
    #print(platform.python_version())


    app = QtGui.QApplication(sys.argv)


    parser = optparse.OptionParser(
        usage='\n\t%prog [file]',
        version='%%prog %s' % __version__)
    parser.add_option(
        '-f', '--filter',
        type='choice', choices=('dot', 'neato', 'twopi', 'circo', 'fdp'),
        dest='filter', default='dot',
        help='graphviz filter: dot, neato, twopi, circo, or fdp [default: %default]')

    (options, args) = parser.parse_args(sys.argv[1:])

    appUI = ApplicationUI()
    appUI.setFilter(options.filter)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
