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
from bp.memory import MemoryFS, MemoryPath, format_memory_path
from bp.tests.test_paths import AbstractFilePathTestCase


def heads(t):
    for i in range(len(t)):
        yield t[:i]


class MemoryPathTestCase(AbstractFilePathTestCase):

    def subdir(self, *dirname):
        for head in heads(dirname):
            self.fs._dirs.add(head)
        self.fs._dirs.add(dirname)

    def subfile(self, *dirname):
        for head in heads(dirname):
            self.fs._dirs.add(head)
        return self.fs.open(dirname)

    def setUp(self):
        self.fs = MemoryFS()

        AbstractFilePathTestCase.setUp(self)

        self.path = MemoryPath(self.fs)
        self.root = self.path
        self.all = self.fs._dirs | set(self.fs._store.keys())
        self.all = set(format_memory_path(p, "/") for p in self.all)

    def test_removeDirectory(self):
        """
        L{MemoryPath.remove} on a L{MemoryPath} that refers to a
        directory will recursively delete its contents.
        """
        self.assertTrue(self.path.isdir())
        self.assertTrue(self.path.exists())

        foo = self.path.child("foo")
        foo.setContent("Hi!")
        baz = self.path.descendant(["bar", "baz"])
        baz.setContent("Bye!")

        self.path.remove()
        self.assertFalse(self.path.exists())
        self.assertFalse(foo.exists())
        self.assertFalse(baz.exists())

    def test_removeFile(self):
        """
        L{MemoryPath.remove} on a L{MemoryPath} that refers to a
        file simply deletes the file.
        """
        path = self.path.child("file")
        path.setContent("Hello!")
        self.assertTrue(path.isfile())
        self.assertTrue(path.exists())

        path.remove()
        self.assertFalse(path.exists())

    def test_removeNonExistant(self):
        """
        L{MemoryPath.remove} on a L{MemoryPath} that does not exist
        raises an error.
        """
        path = self.path.child("file")
        self.assertFalse(path.exists())

        with self.assertRaises(Exception):
            path.remove()
