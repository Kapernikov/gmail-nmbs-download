import imaplib
import re
import quopri
import sys

username = sys.argv[1]
password = sys.argv[2]
tsfx = sys.argv[3]

imap_server = imaplib.IMAP4_SSL("imap.gmail.com", 993)
imap_server.login(username, password)

imap_server.select('INBOX')

# Count the unread emails
status, response = imap_server.status('INBOX', "(UNSEEN)")
unreadcount = int(response[0].split()[2].strip(').,]'))
print "unread: %i " % unreadcount


def get_email(id):
        _, response = imap_server.fetch(id, '(UID BODY[TEXT])')
        return response[0][1]

def get_headers(id):
        _, response = imap_server.fetch(id, '(UID BODY[HEADER])')
        from email.parser import HeaderParser
        hp = HeaderParser()
        return hp.parsestr(response[0][1])


def get_date(id):
        import datetime
        _, response = imap_server.fetch(id, '(UID INTERNALDATE)')
        return imaplib.Internaldate2tuple(response[0])
        
                
def get_subject(id):
        _, response = imap_server.fetch(id, '(body[header.fields (subject)])')
        return  response[0][1][9:]

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
        subjects.append(response[0][1][9:])
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
            k = l.replace("Het artikel staat op naam van ", "")
            k = k.replace(" en wordt afgeleverd op uw elektronische identiteitskaart.", "")
            k = k.replace(" en wordt afgeleverd in pdf formaat.", "")
            return k


def findType(body):
    bb = body
    bb = body.replace("VERVOER VAN HUISDIEREN", "HUISDIEREN")
    x = re.compile("Artikel van het type ([A-Z]+) (Heen en Terug|Enkel), geldig in (.+) klas van (.+) naar (.+) op (.+) voor de prijs van (.+) EUR.")
    return x.findall(bb)[0]
    
def getFrom(type):
	return type[3].replace("ZONE ", "").replace("LEUVEN", "LVN").replace("BRUSSEL", "BXL")

def getTo(type):
	return type[4].replace("ZONE ", "").replace("LEUVEN", "LVN").replace("BRUSSEL", "BXL")

def findPrice(body):
    for l in body.splitlines():
        if "De totale prijs van de bestelling bedraagt " in l:
            k = l.replace("De totale prijs van de bestelling bedraagt ", "")
            k = k.replace(" EUR en wordt betaald door:", "")
            k = k.replace(" en wordt betaald door:", "")
            return k

def findReferentie(subjectline):
        x = re.compile("N ([0-9]+) ")
        return x.findall(subjectline)[0]

def getDateString(date):
	dd = date[0:2]
	mm = date[3:5]
	yyyy = date[6:10]
	return "%s%s%s" % (yyyy , mm, dd)

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

nb_er = 0
import csv

c = csv.writer(open("tickets-%s.csv" % tsfx, "wb"))
c.writerow(["date", "reference", "OPA", "FROM", "TO", "price", "who", "betaald", "type"])
for id in emails_from("ticketonline"):
    body = quopri.decodestring(get_email(id))
    subject = quopri.decodestring(get_subject(id))
#	headers = get_headers(id)
    import time
    msgdate = time.strftime("%Y%m%d", get_date(id))
    try:
        opa = findOPA(body)
        bestel = findOrder(body).replace(" ", "")
        who = findWho(body)
        betaald = findBetaaldDoor(body)
        price = findPrice(body)
        type = findType(body)
        ref = findReferentie(subject)
        suffix = ""
        if (type[1] != "Enkel"):
            suffix = "-T"
        c.writerow([time.strftime("%d/%m/%Y", get_date(id)), ref, opa, getFrom(type), getTo(type), price, who, betaald, type[1] ])
        basename = "tickets/%s - NMBS - N%s OPA%s - %s-%s%s %s %s" % (msgdate, ref, opa, getFrom(type), getTo(type), suffix , type[6].replace(",", ""), tsfx)
        f = open("%s.txt" % basename, "w")
        f.write(body)
        f.close()
        import os
        os.system("enscript -r -B -2 -o '%s.ps'  '%s.txt'" % (basename, basename))
        os.system("ps2pdf '%s.ps' '%s.pdf'" % (basename, basename))
        os.system("rm '%s.txt' '%s.ps'" % (basename, basename))
        print [opa, bestel, who, betaald, price, type]
	
    except:
        print "ERROR !!!"
        basename = "errors/%i" % nb_er
        f = open("%s.txt" % basename, "w")
        f.write(subject)
        f.write("\n\n")
        import sys
        f.write("%s %s %s\n\n" % sys.exc_info())
        f.write(body)
        f.close()
        nb_er = nb_er + 1

#c.close()
