# Copyright (C) 2014 Seagate Technology.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

#@author: Ignacio Corderi

import kinetic_pb2 as messages

MAX_KEY_SIZE = 4*1024
MAX_VALUE_SIZE = 1024*1024

class Entry(object):

    #RPC: Note, you could build this as a class method, if you wanted the fromMessage to build
    #the subclass on a fromMessage. I suspect you always want to generate Entry objects,
    #in which case, a staticmethod is appropriate as a factory.
    @staticmethod
    def fromMessage(header, value):
        if not header: return None
        return Entry(header.command.body.keyValue.key, value, EntryMetadata.fromMessage(header))

    @staticmethod
    def fromResponse(header, value):
        if (header.command.status.code == messages.Message.Status.SUCCESS):
            return Entry.fromMessage(header, value)
        elif (header.command.status.code == messages.Message.Status.NOT_FOUND):
            return None
        else:
            raise KineticMessageException(header.command.status)

    def __init__(self, key, value, metadata=None):
        self.key = key
        self.value = value
        self.metadata = metadata or EntryMetadata()

    def __str__(self):
        if self.value:
            return "{key}={value}".format(key=self.key, value=self.value)
        else:
            return self.key

class EntryMetadata(object):

    @staticmethod
    def fromMessage(msg):
        if not msg: return None
        return EntryMetadata(msg.command.body.keyValue.dbVersion, msg.command.body.keyValue.tag,
                             msg.command.body.keyValue.algorithm)

    def __init__(self, version=None, tag=None, algorithm=None):
        self.version = version
        self.tag = tag
        self.algorithm = algorithm

    def __str__(self):
        return self.version or "None"

class KeyRange(object):

    def __init__(self, startKey, endKey, startKeyInclusive=True,
                 endKeyInclusive=True):
        self.startKey = startKey
        self.endKey = endKey
        self.startKeyInclusive = startKeyInclusive
        self.endKeyInclusive = endKeyInclusive

    def getFrom(self, client, max=1024):
        return client.getKeyRange(self.startKey, self.endKey, self.startKeyInclusive, self.endKeyInclusive, max)

class P2pOp(object):

    def __init__(self, key, version=None, newKey=None, force=None):
        self.key = key
        self.version = version
        self.newKey = newKey
        self.force = force

class Peer(object):

    def __init__(self, hostname='localhost', port=8123, tls=None):
        self.hostname = hostname
        self.port = port
        self.tls = tls

# Exceptions

class KineticException(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class KineticClientException(KineticException):
    pass

class NotConnected(KineticClientException):
    pass

class AlreadyConnected(KineticClientException):
    pass

class ServerDisconnect(KineticClientException):
    pass

class ConnectionFaulted(KineticClientException):
    pass

class ConnectionClosed(KineticClientException):
    pass

class KineticMessageException(KineticException):

    def __init__(self, status):
        self.value = status.statusMessage
        self.status = status
        self.code = self.status.DESCRIPTOR.enum_types[0]\
                .values_by_number[self.status.code].name

    def __str__(self):
        return self.code + (': %s' % self.value if self.value else '')

class Synchronization:
    INVALID_SYNCHRONIZATION = -1
    WRITETHROUGH = 1 # Sync
    WRITEBACK = 2 # Async
    FLUSH = 3

class IntegrityAlgorithms:
    SHA1 = 1
    SHA2 = 2
    SHA3 = 3
    CRC32 = 4
    CRC64 = 5
    # 6-99 are reserverd.
    # 100-inf are private algorithms

class LogTypes:
    INVALID_TYPE = -1
    UTILIZATIONS = 0
    TEMPERATURES = 1
    CAPACITIES = 2
    CONFIGURATION = 3
    STATISTICS = 4
    MESSAGES = 5
    LIMITS = 6

    @classmethod
    def all(cls):
        """
            LogTypes.all takes no arguments and returns a list of all valid log magic numbers (from the protobuf definition)
            that can be retrieved using the AdminClient .getLog method. Log types avaiable are: (0-> Utilizations, 1-> Temperatures,
            2->Drive Capacity, 3-> Drive Configuration, 4->Drive usage statistics, and 5-> Drive messages). This can be passed as
            the sole argument to the AdminClient.getLog function.
        """
        return [cls.UTILIZATIONS, cls.TEMPERATURES, cls.CAPACITIES, cls.CONFIGURATION, cls.STATISTICS, cls.MESSAGES, cls.LIMITS]