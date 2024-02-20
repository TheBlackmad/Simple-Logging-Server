# Simple-Logging-Server
This repository contains a network logging server, base on logging cookbook

This logging server is taken as the example from the https://docs.python.org/3/howto/logging-cookbook.html website.
The parts modified in this programs are related the handling of the LogRecord received from the network.
Method LogRecordStreamHandler::handleLogRecord modified to support the logging of records under /var/log/ base log
folder using a TimedRotating policy every day, keeping files for 1 week back. The name of the logger shall be in the form

<app_name>.<function_name>

where 

<app_name> - app name will be used for creating a folder under the base log folder
<function_name> - function name will be used as the log file

