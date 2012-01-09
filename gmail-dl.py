import imaplib
import re
import quopri
import sys

username=sys.argv[1]
password=sys.argv[2]


imap_server = imaplib.IMAP4_SSL("imap.gmail.com",993)
imap_server.login(username, password)

imap_server.select('INBOX')

# Count the unread emails
status, response = imap_server.status('INBOX', "(UNSEEN)")
unreadcount = int(response[0].split()[2].strip(').,]'))
print "unread: %i " % unreadcount


def get_email(id):
        _, response = imap_server.fetch(id, '(UID BODY[TEXT])')
        return response[0][1]
                

def get_emails(email_ids):
    data = []
    for e_id in email_ids:
        _, response = imap_server.fetch(e_id, '(UID BODY[TEXT])')
        data.append(response[0][1])
    return data

def get_subjects(email_ids):
    subjects = []
    for e_id in email_ids:
        _, response = imap_server.fetch(e_id, '(body[header.fields (subject)])')
        subjects.append( response[0][1][9:] )
    return subjects

def emails_from(name):
    '''Search for all mail from name'''
    status, response = imap_server.search(None, '(FROM "%s")' % name)
    email_ids = [e_id for e_id in response[0].split()]
    return email_ids

def findOPA(body):
    for l in body.splitlines():
        if "OPA-nummer" in l:
            return l.split(":")[1]

def findOrder(body):
    for l in body.splitlines():
        if "Bestelnummer:" in l:
            return l.split(":")[1]

def findHow(body):
    if "wordt afgeleverd op uw elektronische identiteitskaart" in body:
        return "IK"
    if "wordt afgeleverd in pdf formaat" in body:
        return "PDF"

def findWho(body):
    for l in body.splitlines():
        if "Het artikel staat op naam van" in l:
            k = l.replace("Het artikel staat op naam van ","")
            k = k.replace(" en wordt afgeleverd op uw elektronische identiteitskaart.","")
            k = k.replace(" en wordt afgeleverd in pdf formaat.","")
            return k


def findType(body):
    x = re.compile("Artikel van het type ([A-Z]+) (Heen en Terug|Enkel), geldig in (.+) klas van (.+) naar (.+) op (.+) voor de prijs van (.+) EUR.")
    return x.findall(body)
    

def findPrice(body):
    for l in body.splitlines():
        if "De totale prijs van de bestelling bedraagt " in l:
            k = l.replace("De totale prijs van de bestelling bedraagt ","")
            k = k.replace(" EUR en wordt betaald door:","")
            k = k.replace(" en wordt betaald door:","")
            return k
def findBetaaldDoor(body):
    bet = -1
    res = ""
    for l in body.splitlines():
        if (bet >= 0):
            bet = bet + 1
            if (len(res) > 0):
                res = res + ", " 
            res += l
        if "en wordt betaald door:" in l:
            bet = 0
        if (bet == 3):
            return res        


for id in emails_from("ticketonline"):
	body = quopri.decodestring(get_email(id))
	opa=  findOPA(body)
	bestel= findOrder(body).replace(" ", "")
	who = findWho(body)
	betaald = findBetaaldDoor(body)
	price = findPrice(body)
	type = findType(body)
	f = open("%s.txt" % bestel, "w")
	f.write(body)
	f.close()
	import os
	os.system("enscript -o %s.ps  %s.txt" % (bestel,bestel))
	os.system("ps2pdf %s.ps %s.pdf" % (bestel,bestel))
	print [opa, bestel, who, betaald,price,type]
	
	