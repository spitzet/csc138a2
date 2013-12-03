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

        (code, response) = self.connect()
        if (code != 220):
            self._logger.info('Could not establish connection to SMTP server')
            raise Exception('Could not establish connection to SMTP server')
        
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
            
            # The response code is always a 3-digit number
            code = int(line[:3])
            
            # Append the response data (no need to store the message)
            response.append(line[4:].strip())

            # Multi-line responses have a "-" character in between the code and response
            if (line[3:4] != '-'):
                break
            else:
                self._logger.info(line)
    
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
		if (response == '354'):
			self._logger.debug('Start mail input; end with <CRLF>.<CRLF>')
		else raise Exception('Error')
        return code, response

    ##
    # EHLO
    ##
    def ehlo(self):
        (code, response) = self.command('EHLO', self.config['localhostname'])
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)
		if (response == '250'):
			self._logger.debug('Successful')
			message = message + "\r\n.\r\n"
		else raise Exception('Error')
        return code, response

    ##
    # EXPN: Expands mailing list 
    ##
    def expn(self, address):
        (code, response) = self.command('EXPN', address)
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)
		if (response == '250'):
			self._logger.debug('Successful')
		else raise Exception('Error')
        self.disconnect()
        return code, response

    ##
    # HELO
    ##
    def helo(self):
        (code, response) = self.command('HELO', self.config['localhostname'])
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)
		if (response == '250'):
			self._logger.debug('Successful')
		else raise Exception('Error')
        return code, response

    ##
    # MAIL: Message from 
    ##
    def mail(self, sender = None):
        sender = sender or self.sender

        (code, response) = self.command('MAIL', 'FROM: ' + sender)
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)
		if (response == '250'):
			self._logger.debug('Successful')
		else raise Exception('Error')
        return code, response

    ##
    # NOOP: Does Nothing
    ##
    def noop(self):
        (code, response) = self.command('NOOP')
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)
		if (response == '250'):
			self._logger.debug('Successful')
		elif (response == '200'):
			self._logger.debug('Nonstandard Success Reponse')
		else raise Exception('Error')
        return code, response

    ##
    # RCPT: Message Recipient
    ##
    def rcpt(self, recipient):
        (code, response) = self.command('RCPT', 'TO: ' + recipient)
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)
		if (response == '250'):
			self._logger.debug('Successful')
		else raise Exception('Error')
        return code, response

    ##
    # QUIT: Quits the SMTP session
    ##
    def quit(self):
        (code, response) = self.command('QUIT')
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)
        self.disconnect()
        return code, response
    
    ##
    # RSET: Resets the current SMTP session
    ##
    def rset(self):
        (code, response) = self.command('RSET')
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)
		if (response == '250'):
			self._logger.debug('Successful')
		elif (response == '200'):
			self._logger.debug('Nonstandard Success Reponse')
		else raise Exception('Error')
        return code, response
    
    ##
    # VRFY: Checks that an address is valid
    ##
    def vrfy(self, address):
        (code, response) = self.command('VRFY', address)
        self._logger.debug('Received ' + str(code) + ' with response: ' + response)
		if (response == '250'):
			self._logger.debug('Successful')
		else raise Exception('Error')
        self.disconnect()
        return code, response


    ##
    # Skeleton for a all-in-one sendmail function
    ##
    def sendmail(self, fromAddr, toAddrs, subject, message):
        self.setFromAddr(fromAddr)
        self.addRecipients(toAddrs)
        self.setSubject(subject)
        self.setMessage(message)
        self.send()
        
        
logging.basicConfig(format='%(levelname)s: %(message)s', level=config['loglevel'])
client = SmtpClient(config);

client.helo()
client.quit()


