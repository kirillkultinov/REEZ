import sys
import r2pipe

class BinaryProcessor:
    r2 = None
    callGraph = None

    def __init__(self, fileName):
        self.r2 = r2pipe.open(str(fileName))
        self.r2.cmd('aa')

    def getCallGraph(self):
        self.callGraph = self.r2.cmd('agC')
        return self.callGraph

    def getCallGraphNoLibs(self):
        return 0

    def disassembleFunction(self, functionName):
        disassembly = self.r2.cmd('pdf@' + functionName)
        return disassembly