# TheBlackmad
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.import pickle
#
# Base File taken from https://docs.python.org/3/howto/logging-cookbook.html
# Method LogRecordStreamHandler::handleLogRecord modified to support the logging
# of records under /var/log/ base log folder using a TimedRotating policy every day,
# keeping files for 1 week back. The name of the logger shall be in the form
#
# <app_name>.<function_name>.
#
# <app_name> - app name will be used for creating a folder under the base log folder
# <function_name> - function name will be used as the log file
#

import pickle
import logging
import logging.handlers
from logging.handlers import TimedRotatingFileHandler
import socketserver
import struct
import os

class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack('>L', chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)
            record = logging.makeLogRecord(obj)
            self.handleLogRecord(record)

    def unPickle(self, data):
        return pickle.loads(data)

    def handleLogRecord(self, record):
        # if a name is specified, we use the named logger rather than the one
        # implied by the record.
        if self.server.logname is not None:
            name = self.server.logname
        else:
            name = record.name
	# a logger need to be retrieve before getting the record being processed.
        logger = self.retrieveLogger(name)
        logger.handle(record)

    def retrieveLogger(self, name):
        # the required logger might be registered already. If this is the case, use it and 
        # if not, create a new one with the handler
        if name not in logging.root.manager.loggerDict:
                self.createLogger(name)
        return logging.getLogger(name)

    def createLogger(self, name):
        # the logger name is formed by the <app_name>.<program_name>
        # log filename will be located under '/var/log/<app_name>/<program_name>
        # creating a rotating timed file handler. folder must be created
        # Although filenames and folders should be created, this is a very basic remote logger
        # for my purposes
        path_fn = "/var/log/" + name[:name.find(".")]
        filename = name[name.find(".")+1:] + ".log"
        if not os.path.exists(path_fn):
            os.makedirs(path_fn)

        logger = logging.getLogger(name)
        new_handler = TimedRotatingFileHandler(path_fn+'/'+filename, when='midnight', interval=1, backupCount=7)
        formatter = logging.Formatter("%(asctime)s - %(filename)s - %(levelname)s - %(funcName)s - Line %(lineno)d - %(message)s")
        new_handler.setFormatter(formatter)
        logger.addHandler(new_handler)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
    Simple TCP socket-based logging receiver suitable for testing.
    """

    allow_reuse_address = True

    def __init__(self, host='192.168.178.60',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler=LogRecordStreamHandler):
        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self):
        import select
        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort

def main():
    logging.basicConfig(
        format='%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s')
    tcpserver = LogRecordSocketReceiver()
    print('About to start TCP server...')
    tcpserver.serve_until_stopped()

if __name__ == '__main__':
    main()

