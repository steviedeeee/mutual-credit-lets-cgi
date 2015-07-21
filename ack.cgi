#!/usr/local/bin/python
# change top line to the path of the Python interpreter on your system

""" ack.cgi This file handles the 2 (ack1.form and ack2.form) 
    forms used to input and then confirm an acknowledgement. 

    Modified 16 May 2003 to split process into 2 forms to allow
    auto buyer/seller names fill in and confirmation, also to 
    report ack_id on successful completion page.

    Richard Kay last changed: 16 May 2003
"""

# uncomment next 3 lines to debug script
#import sys
#sys.stderr=sys.stdout
#print "Content-type: text/plain\n"

import cgiutils
import tablcgi
from table_details import btab,mtab,atab

# globals
members=None
# change following line to 0 to allow account holders to pay from own a/c
# change following line to 1 to allow only admin account to make payment
# change following line to 2 to allow any account holders to pay from any a/c
admin_only=1

def next_ackid():
  ''' gets an ackid for a new ack and increments registry counter'''
  from table_details import naid
  import pickle
  import LockFile
  lockfilename=naid.file+".lock"
  lock=LockFile.LockFile(lockfilename,withlogging=1)
  try:
    try:
      lock.lock(15)
      rp=open(naid.file,"r")
      nextnum=pickle.load(rp)
      rp.close()
      wp=open(naid.file,"w")
      pickle.dump(nextnum+1,wp)
      wp.close()
    finally:
      lock.unlock()
  except LockFile.LockError:
    errormes="could not get exclusive lock on next ackid file"
    raise errormes 
  return nextnum

def main():
  cgiutils.html_header(title="LETS Accounting acknowledgement processing")
  confirmation_needed=0
  if len(cgiutils.keys()) == 0:
    # if no keys authentication data missing
    cgiutils.html_end(error="Missing authentication details.")
    return
  elif cgiutils.has_required(["ac_id","pin","from_id",
        "to_id","amount","details"]) and not cgiutils.has_required(
	["from_name","to_name"]):
    # input is from ack1.form, create and send ack2.form (confirmation) 
    confirmation_needed=1 
  elif not cgiutils.has_required(["ac_id","pin","from_id",
      "from_name","to_id","to_name","amount","details"]):
    cgiutils.html_end(error="Missing value/s. Complete all form fields.")
    return
  # check if has required keys and of correct format 
  ac_id=cgiutils.firstval("ac_id")
  pinentry=cgiutils.firstval("pin")
  # check field formats 
  if not cgiutils.is_valid(ac_id,max_leng=8,allowed='^[\w]+$'):
    cgiutils.html_end(error="Invalid user account id/no.")
    return
  if not cgiutils.is_valid(pinentry,allowed='^[1-9][0-9]{3,3}$'):
    cgiutils.html_end(error="Invalid PIN format.")
    return
  # check if account is admin and admin_only
  if admin_only==1 and not ac_id == "admin":
    cgiutils.html_end(error="Only the administrator is allowed to do this.")
    return
  # check pin 
  members=tablcgi.table(mtab)
  balance=tablcgi.table(btab)
  ismember=members.has_key(ac_id)
  if not ismember:
    cgiutils.html_end(error="Account no./id not found.")
    return
  else:
    index=members.find(ac_id)
    pin=members.data[index]["pin"]
  if int(pinentry) != int(pin):
    cgiutils.html_end(error="Incorrect PIN entered.")
    return
  # validate other fields
  from_id=cgiutils.firstval("from_id")
  if not cgiutils.is_valid(from_id,max_leng=8,allowed='^[\w]+$'):
    cgiutils.html_end(error="Invalid from account id/no.")
    return
  fmember=members.has_key(from_id)
  if not fmember:
    cgiutils.html_end(error="From Account no./id not found.")
    return
  if not balance.has_key(from_id):
    error="""from a/c has member record but no balance record. 
      please inform webmaster."""
    cgiutils.html_end(error)
    return
  if admin_only == 0 and to_id != ac_id:
    cgiutils.html_end(error="You can only pay out of your own account.")
    return
  to_id=cgiutils.firstval("to_id")
  findex=members.find(from_id)
  if members.data[findex]["active"] != 'Y':
    cgiutils.html_end(error="From Account is inactive.")
    return
  if not cgiutils.is_valid(to_id,max_leng=8,allowed='^[\w]+$'):
    cgiutils.html_end(error="Invalid to account id/no.")
    return
  tmember=members.has_key(to_id)
  if not tmember:
    cgiutils.html_end(error="To Account no./id not found.")
    return
  tindex=members.find(to_id)
  if members.data[tindex]["active"] != 'Y':
    cgiutils.html_end(error="To Account is inactive.")
    return
  if not balance.has_key(to_id):
    error="""To a/c has member record but no balance record. 
      please inform webmaster."""
    cgiutils.html_end(error)
    return
  amount=cgiutils.stof("amount")
  if type(amount) == type(None):
    cgiutils.html_end(error="Invalid amount, not numeric.")
    return
  if amount < 0.0 or amount > 1000.0:
    cgiutils.html_end(error="Invalid amount, negative or too large.")
    return
  details=cgiutils.firstval("details")
  if not cgiutils.is_valid(details,max_leng=60,
    allowed=r'''^[\w \'\-\.\,\!\"\'\£\$\%\^\&\*\(\)\+\=\;\:\?\/\\\@\|]+$'''):
    cgiutils.html_end(error="Invalid details.")
    return
  if confirmation_needed:
    # send ack2 confirmation form with names filled in
    from_name=members.data[findex]["name"] 
    to_name=members.data[tindex]["name"]
    string_amount=cgiutils.firstval("amount") # need string not float type
    # send the ack2.form
    cgiutils.send_form("ack2.form",[ac_id,pin,to_name,to_id,
      from_name,from_id,string_amount,details])
    cgiutils.html_end(want_form=1)
    return
  from_name=cgiutils.firstval("from_name")
  if not cgiutils.is_valid(from_name,max_leng=60,
      allowed='^[A-Za-z][\w\'\- ]+$'):
    cgiutils.html_end(error="Invalid From name.")
    return
  to_name=cgiutils.firstval("to_name")
  if not cgiutils.is_valid(to_name,max_leng=60,
      allowed='^[A-Za-z][\w\'\- ]+$'):
    cgiutils.html_end(error="Invalid To name.")
    return
  import time
  acktime=int(time.time())
  try:
    ack_id=next_ackid()
  except:
    error="""Couldn't obtain next ack_id. File locking problem ? 
       Try again in a few minutes and if you have the same problem 
       repeatedly please inform the webmaster."""
    cgiutils.html_end(error)
    return
  arow={"ack_id":ack_id,
        "from_id":from_id,
        "from_name":from_name,
        "to_id":to_id,
        "to_name":to_name,
	"amount":amount,
        "system":"main",
	"details":details,
        "time":acktime}
  acks=tablcgi.table(atab)
  # transfer payment between accounts and add ack record to journal
  tindex=balance.find(to_id)
  findex=balance.find(from_id)
  balance.data[findex]["balance"]-=amount
  balance.data[findex]["out"]+=amount
  balance.data[findex]["turnover"]+=amount
  balance.data[tindex]["balance"]+=amount
  balance.data[tindex]["in"]+=amount
  balance.data[tindex]["turnover"]+=amount
  acks.addrow(arow)
  balance.save()
  print "<p> Acknowledgment: "+str(ack_id)+" successfully input.</p>" 
  cgiutils.html_end(received=1)
  return 

if __name__ == "__main__":
  try: 
    main()
  except:
    import traceback
    print "error detected in ack.cgi main()"
    traceback.print_exc()

