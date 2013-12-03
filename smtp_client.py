##
# Programming Assignment 2
# CPE 138, Fall 2013
# California State University, Sacramento
#
# This is SMTP client
#
# Created by Greg M. Crist, Jr. <gmcrist@gmail.com> & Travis Spitze <travissp87@gmail.com>
##

import base64       # For base 64 encoding of username/password for smtp authentication 
import logging      # For logging / debug messages
import re           # Regular Expressions
import socket       # Network socket coding
import ssl          # SSL code
import time         # Date / time functions


# Default configuration for the server
config = {
    'host': 'smtp.gmail.com',
    'port': '25',
    'ssl': False,
    'username': 'username@gmail.com',
    'password': 'password',
    'loglevel': logging.DEBUG
}

message = {
    'sender': 'sender@example.com',
    'recipients': ['recipient@example.com'],
    'body': "From: sender@example.com\r\nSubject: Test for CPE 138\r\n\r\nThis is a test\r\n"
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

        (code, response) = self.connect()
        if (code != 220):
            raise Exception('Could not establish connection to SMTP server')
        
        # RFC 2821 requires us to use the fully qualified domain name for the EHLO/HELO commands
        fqdn = socket.getfqdn()

        if ('.' in fqdn):
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

        if (self.config['ssl']):
            self._logger.info('Establishing TLS connection')
            (code, response) = self.command('STARTTLS')
            
            if (code != 220):
                raise Exception('Error starting TLS: ' + code + ' ' + response)

            self.socket = ssl.wrap_socket(self.socket, ssl_version = ssl.PROTOCOL_SSLv23)
        
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
        if (self.socket):
            try:
                self.socket.sendall(data)
            except socket.error:
                self._logger.error('Error sending data to socket')
                self.disconnect()
                raise Exception('error sending data to socket')
        else:
            self._logger.error('no socket connection')
            raise Exception('no socket connection')

    ##
    # Execute SMTP command and get response
    ##
    def command(self, command, data = None):
        if (data is None):
            self._logger.debug('Sending command "' + command + '" to SMTP server')
            data = command + "\r\n"
        else:
            self._logger.debug('Sending command "' + command + '" with data "' + data + '" to SMTP server')
            data = command + ' ' + data + "\r\n"
        
        self.send(data)
        return self.response()

    ##
    # Get repsponse from SMTP server
    ##
    def response(self):
        response = []
        
        try:
            data = self.socket.recv(1024)

        except socket.error:
            self._logger.error('Connection to SMTP server closed unexpectedly')
            self.disconnect()
            raise Exception('Connection to SMTP server closed unexpectedly')
        
        # The response code is always a 3-digit number
        code = int(data[:3])
        
        # Append the response data (no need to store the message)
        response.append(data[4:].strip())

        return code, "\n".join(response)


    #################
    # SMTP Commands #
    #################

    ##
    # DATA: Sends Message Data
    ##
    def data(self, message):
        (code, response) = self.command('DATA')
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)

        if (code != 354):
            raise Exception('Error with DATA command: ' + code + ' ' + response)

        # Handle invalid line endings and lines starting with a data end sequence
        message = re.sub(r'(?m)^\.', '..', re.sub(r'(?:\r\n|\n|\r(?!\n))', message, "\r\n"))

        # Send the message and data end sequence
        self.send(message)
        self.send("\r\n.\r\n")

        return self.response()

    ##
    # EHLO
    ##
    def ehlo(self):
        (code, response) = self.command('EHLO', self.config['localhostname'])
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)

        if (code != 250):
            raise Exception('Error with EHLO command: ' + code + ' ' + response)

        return code, response

    ##
    # HELO
    ##
    def helo(self):
        (code, response) = self.command('HELO', self.config['localhostname'])
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)

        if (code != 250):
            raise Exception('Error with HELO command: ' + code + ' ' + response)

        return code, response

    ##
    # MAIL: Message from 
    ##
    def mail(self, sender = None):
        sender = sender or self.sender

        (code, response) = self.command('MAIL', 'FROM: ' + sender)
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)

        if (code != 250):
            raise Exception('Error with MAIL command: ' + code + ' ' + response)

        return code, response

    ##
    # RCPT: Message Recipient
    ##
    def rcpt(self, recipient):
        (code, response) = self.command('RCPT', 'TO: ' + recipient)
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)

        if (code != 250):
            raise Exception('Error with RCPT command: ' + code + ' ' + response)

        return code, response

    ##
    # QUIT: Quits the SMTP session
    ##
    def quit(self):
        (code, response) = self.command('QUIT')
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)

        if (code != 221):
            raise Exception('Error with QUIT command: ' + code + ' ' + response)

        self.disconnect()
        return code, response

    ##
    # SMTP Authentication
    ##
    def login(self, username = None, password = None, method = 'PLAIN'):
        username = username or self.config['username']
        password = password or self.config['password']
        
        # Only implementing AUTH_LOGIN
        (code, response) = self.command('AUTH', 'LOGIN ' + base64.b64encode(username))
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)

        if (code != 334):
            raise Exception('AUTH LOGIN command not successful')
        
        (code, response) = self.command(base64.b64encode(password))
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)
        
        # 235 - Authentication Successful, 503 - Already authenticated
        if (code not in (235, 503)):
            self._logger.debug('AUTH LOGIN failed')
            raise Exception('AUTH LOGIN failed')

        return code, response

    ##
    # sendmail function
    ##
    def sendmail(self, sender, recipients, message):
        (code, response) = self.ehlo()
        if (code != 250):
            raise Exception()
        
        (code, response) = self.mail(sender)
        if (code != 250):
            raise Exception()

        # Handle single recipient
        if (isinstance(recipients, basestring)):
            recipients = [recipients]

        recipient_errors = []

        for recipient in recipients:
            (code, response) = self.rcpt(recipient)
            self._logger.debug('Received ' + str(code) + ' with response: ' + response)

            if (code not in (250, 251)):
                recipient_errors[recipient] = (code, response)

        if (len(recipient_errors) < len(recipients)):
            (code, response) = self.data(message)
            self._logger.debug('Received ' + str(code) + ' with response: ' + response)
            
            if (code != 250):
                raise Exception('Error sending message') 

        return recipient_errors


        
logging.basicConfig(format='%(levelname)s: %(message)s', level=config['loglevel'])
client = SmtpClient(config)

try:
    client.login()
    errors = client.sendmail(message['sender'], message['recipients'], message['body'])

    for recipient in errors:
        print 'Error sending to recipient "' + recipient + '", received error:'

except Exception as e:
    print e

