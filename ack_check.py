#!/usr/local/bin/python
# change top line to the path of the Python interpreter on your system

""" ack_check.py This file contains means to
    create a summary from ack records, which can
    be compared against balance records.
    Richard Kay last changed: 23 Aug 2002
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


def summary(option,members):
  # checks whether requested summary file/table is more than 1 day old. If so
  # it is updated and saved. It is then displayed.
  pass
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
      if (option == 'active' and active == 'Y') or option == 'all': 
        srow={}
        for key in ["ac_id","cfwd","balance"]:
          srow[key]=row[key]
        for key in ["in","out","turnover"]:
          srow[key]=0.0
        sumry.addrow(srow)
    # update summary records In Out and Turnover
    for ack in acks.keys():
      aindex=acks.find(ack)
      from_id=acks.data[aindex]["from_id"]
      to_id=acks.data[aindex]["to_id"]
      amount=acks.data[aindex]["amount"]
      from_idx=sumry.find(from_id)
      to_idx=sumry.find(to_id)
      if from_idx != -1: # unless all, only summarise active accounts 
        sumry.data[from_idx]["out"]-=amount
        sumry.data[from_idx]["turnover"]+=abs(amount)
      if to_idx != -1: # unless all, only summarise active accounts 
        sumry.data[to_idx]["in"]+=amount
        sumry.data[to_idx]["turnover"]+=abs(amount)
    # make sumry saveable by restoring filenames and save it
    sumry.file=sfdo.file
    sumry.lockfilename=sumry.file+'.lock'
    sumry.save()
  # end if summary file more than one day old 
  # reopen and read summary file
  sumary=tablcgi.table(sfdo)
  # output to browser
  print """<p>This summary may not include some payments made within 
           the last hour. The file from which this data is taken
           is recreated when a summary request is made and the last
           summary displayed is more than 1 hour old. This design
           choice was adopted in order to reduce unneccessary processing 
           overhead on the server. Note that a balance enquiry should
           give up to the minute details of the account balance, but may
           contain in,out and turnover details up to 1 hour old.<p>""" 
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

