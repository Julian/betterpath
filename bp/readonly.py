from zope.interface import implementer

from bp.abstract import IFilePath
from bp.better import AbstractFilePath
from bp.util import modeIsWriting

@implementer(IFilePath)
class ReadOnlyPath(AbstractFilePath):
    """
    An IFilePath which is intrinsically read-only in every aspect.
    """

    def __init__(self, fp):
        self._fp = fp

        self.sep = self._fp.sep
        self.path = self._fp.path

    def __repr__(self):
        return "ReadOnlyPath(%r)" % (self._fp,)

    def __cmp__(self, other):
        if not isinstance(other, ReadOnlyPath):
            return NotImplemented
        return cmp(self._fp, other._fp)

    def listdir(self):
        return self._fp.listdir()

    # IFilePath navigation

    def parent(self):
        return ReadOnlyPath(self._fp.parent())

    def child(self, name):
        return ReadOnlyPath(self._fp.child(name))

    # IFilePath segments

    def basename(self):
        return self._fp.basename()

    # IFilePath "writing" and reading

    def open(self, mode="r"):
        if modeIsWriting(mode):
            raise Exception("Path is read-only")
        return self._fp.open(mode)

    def createDirectory(self):
        raise Exception("Path is read-only")

    def getContent(self):
        return self._fp.getContent()

    def setContent(self, content, ext=b'.new'):
        raise Exception("Path is read-only")

    # IFilePath stat and other queries

    def changed(self):
        self._fp.changed()

    def isdir(self):
        return self._fp.isdir()

    def isfile(self):
        return self._fp.isfile()

    def islink(self):
        return self._fp.islink()

    def exists(self):
        return self._fp.exists()

    def getsize(self):
        return self._fp.getsize()

    def getModificationTime(self):
        return self._fp.getModificationTime()

    def getStatusChangeTime(self):
        return self._fp.getStatusChangeTime()

    def getAccessTime(self):
        return self._fp.getAccessTime()

    # Symlinks

    def realpath(self):
        return ReadOnlyPath(self._fp.realpath())
