# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from MetaArray import MetaArray
from numpy import ndarray
from .FileType import FileType

#class MetaArray(FileType):
    #@staticmethod
    #def write(self, dirHandle, fileName, **args):
        #self.data.write(os.path.join(dirHandle.name(), fileName), **args)
        
    #@staticmethod
    #def extension(self, **args):
        #return ".ma"
        
#def fromFile(fileName, info=None):
    #return MetaArray(file=fileName)



class MetaArray(FileType):
    
    extensions = ['.ma']   ## list of extensions handled by this class
    dataTypes = [MetaArray, ndarray]    ## list of python types handled by this class
    priority = 100      ## High priority; MetaArray is the preferred way to move data..
    
    @classmethod
    def write(cls, data, dirHandle, fileName, **args):
        """Write data to fileName.
        Return the file name written (this allows the function to modify the requested file name)
        """
        ext = cls.extensions[0]
        if fileName[-len(ext):] != ext:
            fileName = fileName + ext
            
        if not isinstance(data, MetaArray):
            data = MetaArray(data)
        data.write(os.path.join(dirHandle.name(), fileName), **args)
        return fileName
        
    @classmethod
    def read(cls, fileHandle, *args, **kargs):
        """Read a file, return a data object"""
        return MetaArray(file=fileHandle.name(), *args, **kargs)
