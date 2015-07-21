#!/usr/local/bin/python
# change top line to the path of the Python interpreter on your system

""" entry.cgi This file is the gateway program for a
    simple LETS accounting CGI
    Richard Kay last changed: 16 May 2003
"""

# uncomment next 3 lines to debug script
#import sys
#sys.stderr=sys.stdout
#print "Content-type: text/plain\n"

import cgiutils
import tablcgi
from table_details import atab,btab,mtab,stab

# globals
members=None

def statement(ac_id): 
  # open balances table to get carry forward amount
  balances=tablcgi.table(btab)
  bal_indx=balances.find(ac_id)
  if bal_indx == -1:
    cgiutils.html_end(error="account has no balance. Please inform webmaster")
    return
  cfwd=balances.data[bal_indx]["cfwd"]
  
  # open acknowledgements table
  acks=tablcgi.table(atab)
  # create statement view table object with new balance field
  st_view_def=tablcgi.table_def(atab)
  st_view_def.file=None
  st_view_def.meta["keys"].append("newbal")
  st_view_def.meta["colheads"].append("Balance")
  st_view_def.meta["formats"].append("%.2f")
  st_view=tablcgi.table(st_view_def)
  balance=cfwd
  for row in acks.data:
    if row["from_id"] == ac_id:
      balance = balance - row["amount"]
      outp = 1
    elif row["to_id"] == ac_id:
      balance = balance + row["amount"]
      outp = 1
    else:
      outp = 0
    if outp:
      row["newbal"] = balance 
      st_view.addrow(row)
  # output to browser 
  st_view.tab2html(skip_cols=["system"])
  cgiutils.html_end(received=1)

def summary(option,members):
  # checks whether requested summary file/table is more than 1 day old. If so
  # it is updated and saved. It is then displayed.
  import os,stat,time
  sfdo=tablcgi.table_def(stab) # clone summary file definition object
  if option == 'all':
    sfdo.file='summary_all.pkl'
  else: # option == active
    sfdo.file='summary_active.pkl'
  import os.path
  no_file=1 # true if file doesn't exist
  if os.path.isfile(sfdo.file):
    no_file=0 # file does exist
    statobj=os.stat(sfdo.file) # statobj is a file status tuple object
    # mtime is float seconds since summary file modified 
    mtime=time.time() - statobj[stat.ST_MTIME]
  if no_file or mtime > (60*60):
    # create if nonexistent or recreate if more than 1 hour old
    print "<p> creating summary file please wait."
    # recreate summary file from balance and ack data
    stabview=tablcgi.table_def(sfdo) # clone summary def object as view,
    # retaining appropriate file name in sfdo.file
    stabview.file=None # update view object in memory only until save
    sumry=tablcgi.table(stabview)
    # open acknowledgements table
    acks=tablcgi.table(atab)
    # open balances table 
    balances=tablcgi.table(btab)
    # copy balance records required to new summary table
    for row in balances.data:
      mindex=members.find(row["ac_id"])
      active=members.data[mindex]["active"] 
      name=members.data[mindex]["name"] 
      if (option == 'active' and active == 'Y') or option == 'all': 
        srow={}
        for key in ["ac_id","cfwd","balance","in","out","turnover"]:
          srow[key]=row[key]
	srow["name"]=name
        sumry.addrow(srow)
    # make sumry saveable by restoring filenames and save it
    sumry.file=sfdo.file
    sumry.lockfilename=sumry.file+'.lock'
    sumry.save()
  # end if summary file more than one day old 
  # reopen and read summary file
  sumary=tablcgi.table(sfdo)
  # output to browser
  sumary.tab2html()
  cgiutils.html_end(received=1)

def send_pin(ac_id,email,members):
  # need to access members table to check if user is a member
  index=members.find(ac_id)
  pin=members.data[index]["pin"]
  # send PIN to address entered
  fromad="covlets_accounts@copsewood.net"
  message="From: Coventry LETS Accounts <"+fromad+">\n"
  to_line="To: %s\n" % email
  message+=to_line
  message+="Subject: Coventry LETS PIN request \n\n"
  message+="Someone (presumably you) entered your account number/id\n"
  message+="and email address requesting a PIN for your account.\n"
  message+="\n"
  pin_line="The PIN needed for access is: %s\n" % pin
  message+=pin_line
  message+="\n"
  message+="If this message is in error please ignore it. However,\n"
  message+="if this error persists please contact abuse@copsewood.net .\n"
  message+="\n"
  cgiutils.send_mail(fromad,email,message)
  print "<p>The PIN for the account has been sent as requested.</p>"
  cgiutils.html_end(received=1)

def main():
  cgiutils.html_header(title="LETS Accounting System")
  
  if len(cgiutils.keys()) == 0:
    # if no keys send the form to the browser 
    cgiutils.send_form("entry.form")
    cgiutils.html_end(want_form=1)
    return
  elif not cgiutils.has_required(["account"]):
    cgiutils.html_end(error="You havn't input your account no. or identifier.")
    return

  # has required keys - process form
  ac_id=cgiutils.firstval("account")
  if not cgiutils.is_valid(ac_id,allowed='^\w+$'):
    cgiutils.html_end(error="Invalid account number/identifier.")
    return 
  # which submit button was pressed ?
  option="none"
  for word in ["statement","balance","active","all","pin","ack","admin"]:
    if cgiutils.has_key(word):
      option=word

  if option=="none": 
    cgiutils.html_end(error="Invalid submit button value.")
    return
  
  # check if a PIN was entered and validate it
  pinentry=cgiutils.firstval("PIN",default="")
  if pinentry and not cgiutils.is_valid(pinentry,allowed='^[1-9][0-9]{3,3}$'):
    cgiutils.html_end(error="Invalid PIN format.")
    return
  # check if account id is for a member
  members=tablcgi.table(mtab)
  ismember=members.has_key(ac_id)
  if not ismember:
    cgiutils.html_end(error="Unknown account.")
    return
  # index member now we have a valid account id 
  index=members.find(ac_id)
  if pinentry:
    # check its the correct PIN for this address
    pin=members.data[index]["pin"]
    if int(pinentry) != int(pin):
      cgiutils.html_end(error="Incorrect PIN entered.")
      return
  elif not option == "pin":
    # Without a valid pin actions other than sending pin are prohibited
    cgiutils.html_end(error="No PIN entered.")
    return
  # If we've got this far, there should either be a valid option and PIN
  # or we have a PIN request.
  if option == "pin":
    # check correct email registered for account entered
    email_entered=cgiutils.firstval("EMAIL",default="")
    email_entered=email_entered.lower()
    email=members.data[index]["email"]
    email=email.lower()
    if email_entered != email:
      cgiutils.html_end(error="Incorrect email address, can't send PIN.")
      return
    send_pin(ac_id,email,members)
    return
  # If we've got this far, there should either be a valid option and PIN
  # or we have a PIN request and valid email.
  elif option == "ack":
    # send the ack1 form
    cgiutils.send_form("ack1.form",[ac_id,pin])
    cgiutils.html_end(want_form=1)
  elif option == "balance":
    # send the balance enquiry form
    cgiutils.send_form("balance.form",[ac_id,pin])
  elif option == "admin":
    # send the administration form
    cgiutils.send_form("admin.form",[ac_id,pin])
  elif option == "statement":
    statement(ac_id) 
  elif option == "active" or option == "all":
    summary(option,members) 
  else:
    # should have trapped this one earlier ???
    cgiutils.html_end(error="Invalid option value (2nd trap).")
  return 


if __name__ == "__main__":
  try: 
    main()
  except:
    import traceback
    print "error detected in entry.cgi main()"
    traceback.print_exc()

