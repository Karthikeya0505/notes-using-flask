import smtplib
from email.message import EmailMessage
def send_mail(to,subject,body):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465) #obj creation for gmail server
    server.login('karthikbond865@gmail.com','mtuh rjpx mtkk dcop') #login to gmail
    msg=EmailMessage() #email format obj creation
    msg['FROM']='karthikbond865@gmail.com'
    msg['TO']=to
    msg['SUBJECT']=subject
    msg.set_content(body)
    server.send_message(msg) #mail sending
    server.close() #closing the server obj