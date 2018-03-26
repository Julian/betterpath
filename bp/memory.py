# Copyright (C) 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from errno import EEXIST, ENOENT
from io import BytesIO
from itertools import chain
import os
import stat

from zope.interface import implementer
import attr

from bp.abstract import IFilePath
from bp.errors import PathError, UnlistableError
from bp.generic import (genericChildren, genericParents, genericSegmentsFrom,
                        genericSibling, genericWalk)

DIR = object()
FILE = object()


class MemoryFile(BytesIO):
    """
    A file-like object that saves itself to an external mapping when closed.
    """

    def __init__(self, store, key, buf=""):
        BytesIO.__init__(self, buf)
        self._target = store, key

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def close(self):
        buf = self.getvalue()
        store, key = self._target
        store[key] = buf
        BytesIO.close(self)


class MemoryFS(object):
    """
    An in-memory filesystem.
    """

    def __init__(self):
        self._store = {}
        self._dirs = set()
        self._uids = {}
        self._links = {}

    def create(self, path):
        if path in self._dirs or path in self._store:
            raise PathError("{0} already exists.".format(path))
        return MemoryFile(self._store, path)

    def open(self, path):
        if path in self._dirs:
            raise Exception("Directories cannot be opened")
        elif path in self._store:
            return MemoryFile(self._store, path, self._store[path])
        else:
            return MemoryFile(self._store, path)

    def chown(self, path, uid=None, gid=None):
        # TODO: gid
        self._uids[path] = uid

    def stat(self, path):
        result = [0] * 10
        result[stat.ST_UID] = self._uids.get(path, os.getuid())
        return os.stat_result(result)


def format_memory_path(path, sep):
    return sep.join(("/mem",) + path)


@implementer(IFilePath)
@attr.s(hash=True)
class MemoryPath(object):
    """
    An IFilePath which shows a view into a MemoryFS.
    """

    _fs = attr.ib(repr=False)
    _path = attr.ib(default=())

    sep = "/"

    @property
    def path(self):
        return format_memory_path(self._path, self.sep)

    def listdir(self):
        """
        Pretend that we are a directory and get a listing of child names.
        """

        if self._path not in self._fs._dirs:
            raise UnlistableError()

        i = chain(self._fs._dirs, self._fs._store.keys())

        # Linear-time search. Could be better.
        p = self._path
        l = len(p) + 1
        ks = [t[-1] for t in i if t[:-1] == p and len(t) == l]

        return ks

    # IFilePath generic methods

    children = genericChildren
    parents = genericParents
    segmentsFrom = genericSegmentsFrom
    sibling = genericSibling
    walk = genericWalk

    # IFilePath navigation

    def parent(self):
        if self._path:
            return MemoryPath(fs=self._fs, path=self._path[:-1])
        else:
            return self

    def child(self, name):
        return MemoryPath(fs=self._fs, path=self._path + (name,))

    def descendant(self, segments):
        return MemoryPath(fs=self._fs, path=self._path + tuple(segments))

    # IFilePath writing and reading

    def create(self):
        return self._fs.create(self._path)

    def open(self, mode="r"):
        return self._fs.open(self._path)

    def createDirectory(self):
        if self._path in self._fs._store:
            raise PathError(EEXIST, self._path)
        self._fs._dirs.add(self._path)

    def getContent(self):
        try:
            return self._fs._store[self._path]
        except KeyError:
            raise PathError(ENOENT, self._path)

    def setContent(self, content, ext=b".new"):
        self._fs._store[self._path] = content

    def remove(self):
        if self.isdir():
            for child in self.children():
                child.remove()
            self._fs._dirs.remove(self._path)
        else:
            try:
                del self._fs._store[self._path]
            except KeyError:
                raise PathError(ENOENT, self._path)

    # IFilePath stat and other queries

    def changed(self):
        pass

    def isdir(self):
        return self._path in self._fs._dirs

    def isfile(self):
        return self._path in self._fs._store

    def islink(self):
        return self in self._fs._links

    def exists(self):
        return self.isdir() or self.isfile()

    def basename(self):
        return self._path[-1] if self._path else ""

    def getsize(self):
        if self._path in self._fs._store:
            return len(self._fs._store[self._path])
        else:
            raise Exception("Non-file has no size")

    def getModificationTime(self):
        return 0.0

    def getStatusChangeTime(self):
        return 0.0

    def getUserID(self):
        return self._fs.stat(self).st_uid

    def getAccessTime(self):
        return 0.0

    # IFilePath symlinks

    def realpath(self):
        return self._fs._links.get(self, self).path

    def dirname(self):
        return self.parent().path

    def linkTo(self, linkFilePath):
        self._fs._links[linkFilePath] = self
