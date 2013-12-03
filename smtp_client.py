##
# Programming Assignment 2
# CPE 138, Fall 2013
# California State University, Sacramento
#
# This is SMTP client
#
# Created by Greg M. Crist, Jr. <gmcrist@gmail.com> & Travis Spitze <travissp87@gmail.com>
##

import logging      # For logging / debug messages
import socket       # Network socket coding
import ssl          # SSL code
import time         # Date / time functions


# Default configuration for the server
config = {
    'host': 'smtp.fireup.net',
    'port': '25',
    'ssl': True,
    'loglevel': logging.DEBUG
}

class SmtpClient ():
    _defaultConfig = {
        'host': 'localhost',
        'port': 25,
        'ssl': False,
        'timeout': socket._GLOBAL_DEFAULT_TIMEOUT,
    }

    def __init__(self, config):
        self.config = dict(self._defaultConfig.items() + config.items())
        self._logger = logging.getLogger('SmtpClient')
        self.file = None
        
        # RFC 2821 requires us to use the fully qualified domain name for the EHLO/HELO commands
        fqdn = socket.getfqdn()

        if '.' in fqdn:
            # We have a valid fqdn
            self.config['localhostname'] = fqdn
        else:
            # If we can't determine the fqdn, we should use an encoded IP address
            addr = '127.0.0.1'
            
            try:
                addr = socket.gethostbyname(socket.gethostname())
            except socket.gaierror:
                pass

            self.config['localhostname'] = '[' + addr + ']'

    ##
    # Connect socket
    ##
    def connect(self):
        self._logger.info('Creating connection to SMTP server ' + self.config['host'] + ' on port ' + str(self.config['port']))
        self.socket = socket.create_connection((self.config['host'], self.config['port']), self.config['timeout'])
        
        return self.response()

    ##
    # Disconnect socket
    ##
    def disconnect(self):
        self._logger.info('Closing connection to SMTP server')
        
        if (self.file):
            self.file.close()
            self.file = None
            
        if (self.socket):
            self.socket.close()
            self.socket = None

    ##
    # Send data to socket
    ##
    def send(self, data):
        self._logger.debug('Sending data to SMTP server')
        if (self.socket):
            try:
                self.socket.sendall(data)
            except socket.error:
                self._logger.error('Error sending data to socket')
                self.disconnect();
                raise Exception('error sending data to socket')
        else:
            self._logger.error('no socket connection')
            raise Exception('no socket connection')

    ##
    # Execute SMTP command and get response
    ##
    def command(self, command, data):
        self._logger.info('Sending command "' + command + '" to SMTP server')
        
        if (data == ''):
            data = command + "\r\n"
        else:
            data = command + ' ' + data + "\r\n"
        
        self.send(data)
        return self.response()

    ##
    # Get repsponse from SMTP server
    ##
    def response(self):
        response = []
        
        # It is easier to use the socket readline method
        if (self.file is None):
            self.file = self.socket.makefile('rb')
        
        while True:
            try:
                line = self.file.readline()
                
            except socket.error:
                self._logger.error('Connection to SMTP server closed unexpectedly');
                self.disconnect();
                raise Exception('Connection to SMTP server closed unexpectedly');
            
            self._logger.debug(line);
            
            
            # The response code is always a 3-digit number
            code = int(line[:3])
            
            # Append the response data (no need to store the message)
            response.append(line[4:].strip())

            # Multi-line responses have a "-" character in between the code and response
            if (line[3:4] != '-'):
                break
    
        return code, "\n".join(response)

    def helo(self):
        (code, response) = self.command('HELO', self.config['localhostname']);
        self._logger.info('Received ' + str(code) + ' response with response: ' + response)

    def ehlo(self):
        (code, response) = self.command('EHLO', self.config['localhostname']);
        
    


    def sendmail(self, fromAddr, toAddrs, subject, message):
        self.setFromAddr(fromAddr)
        self.addRecipients(toAddrs)
        self.setSubject(subject)
        self.setMessage(message)
        self.send()
        
        
logging.basicConfig(format='%(levelname)s:%(message)s', level=config['loglevel'])
client = SmtpClient(config);

client.connect();
client.helo();

