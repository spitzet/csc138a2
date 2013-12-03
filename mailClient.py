from socket import *
import base64
import ssl


#author Thi Cao and Kalindi Mehta	


msg = "\r\n This is a testing message for csc138 class assignment!!!"
endmsg = "\r\n.\r\n"

# choose a mail server 
serverName = "smtp.gmail.com"
serverPort = 587
# create socket called clientSocket and establish a TCP connection with the mailserver
clientSocket = socket(AF_INET,SOCK_STREAM)
clientSocket.connect((serverName,serverPort))

recv = clientSocket.recv(1024)
print recv
if recv[:3] != '220' :
	print '220 reply not received from server.'

# send EHLO command and print server response
ehloCommand = 'EHLO Kalindi&Thi\r\n'
clientSocket.send(ehloCommand)
recv1 = clientSocket.recv(1024)
print recv1
if recv1[:3] != '250' :
	print '250 reply not received from server'

# send STARTTLS
startTLSCommand = 'STARTTLS\r\n'
clientSocket.send(startTLSCommand)
recv0 = clientSocket.recv(1024)
print recv0
if recv0[0:3] != '220' :
	print '220 reply not recieved from server'

# use ssl wrap the connected socket
sclientSocket = ssl.wrap_socket(clientSocket,ssl_version = ssl.PROTOCOL_SSLv23)
sclientSocket.send(ehloCommand)
recv00 = sclientSocket.recv(2048)
print recv00 

# send AUTH LOGIN command
authCommand = 'AUTH LOGIN\r\n'
sclientSocket.send(authCommand)
recv2 = sclientSocket.recv(1024)
print recv2
if recv2[:3] != '334' :
	print '334 reply not received from server'
#send BASE64 encoded username
username = 'kalindithi138'
usernameEncode = base64.b64encode(username)
usernameEncode = usernameEncode + '\r\n'
sclientSocket.send(usernameEncode)
recv3 = sclientSocket.recv(1024)
print recv3
if recv3[:3] != '334' :
	print '334 reply not received from server'
	
# send BASE64 encoded password
password = 'pythoncsc138'
passwordEncode = base64.b64encode(password)
passwordEncode = passwordEncode + '\r\n'
sclientSocket.send(passwordEncode)
recv4 = sclientSocket.recv(1024)
print recv4
if recv4[:3] != '235' :
	print '235 reply not recieved from server'
	
# send MAIL FROM command and print server response
mailCommand = 'MAIL FROM: <kalindithi138@gmail.com>\r\n'
sclientSocket.send(mailCommand)
recv5 = sclientSocket.recv(1024)
print recv5
if recv5[:3] != '250' :
	print '250 reply not received from server'
	
# send RCPT TO command and print server response

rcptCommand = 'RCPT TO: <thikalindi138@yahoo.com>\r\n'
sclientSocket.send(rcptCommand)
recv6 = sclientSocket.recv(1024)
print recv6
if recv6[:3] != '250' :
	print '250 reply not received from server'
	

	
#send DATA command and print server
dataCommand = 'DATA\r\n'
sclientSocket.send(dataCommand)
recv7 = sclientSocket.recv(1024)
print recv7
if recv7[:3] != '354' :
	print '354 reply not received from server'
	
#subject command and print server
subjectCommand = 'Subject: Testing message \r\n'
sclientSocket.send(subjectCommand)

	
	
#send message data
sclientSocket.send(msg)

	
# message ends with a single period
sclientSocket.send(endmsg)
recv8 = sclientSocket.recv(1024)
print recv8
if recv8[:3] != '250' :
	print '250 reply not received from server'
	
print mailCommand	
print rcptCommand
print subjectCommand
print msg 

#send QUIT command and get server respond
quitCommand = 'QUIT\r\n'
sclientSocket.send(quitCommand)
recv9 = sclientSocket.recv(1024)
print recv9
if recv9[:3] != '221' :
	print '221 reply not received from server'




