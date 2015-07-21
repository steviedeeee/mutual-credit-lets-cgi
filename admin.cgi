#!/usr/local/bin/python
# change top line to the path of the Python interpreter on your system

""" admin.cgi This file handles input from the account administrators
    form used to create/delete/view/mark inactive accounts.
    Richard Kay last changed: 21 Feb 2003

    Changes: 21 Feb 2003: added facility to modify member details

"""

# uncomment next 3 lines to debug script
#import sys
#sys.stderr=sys.stdout
#print "Content-type: text/plain\n"

import cgiutils
import tablcgi
from table_details import btab,mtab

# globals
members=None

def main():
  cgiutils.html_header(title="LETS Accounting administration results")
  if len(cgiutils.keys()) == 0:
    # if no keys authentication data missing
    cgiutils.html_end(error="Missing authentication details.")
    return
  elif not cgiutils.has_required(["ac_id","pin","user_ac_id"]):
    cgiutils.html_end(error="Missing account identifier or PIN.")
    return

  # check if has required keys and of correct format
  ac_id=cgiutils.firstval("ac_id")
  pinentry=cgiutils.firstval("pin")
  user_ac_id=cgiutils.firstval("user_ac_id")
  # only do work for the admin account
  if not cgiutils.is_valid(ac_id,allowed='^admin$'):
    cgiutils.html_end(error="Only the administrator is allowed to do this.")
    return
  if not cgiutils.is_valid(pinentry,allowed='^[1-9][0-9]{3,3}$'):
    cgiutils.html_end(error="Invalid PIN format.")
    return
  # check user account no./id
  if not cgiutils.is_valid(user_ac_id,max_leng=8,allowed='^[\w]+$'):
    cgiutils.html_end(error="Invalid user account id/no.")
    return

  # check pin
  members=tablcgi.table(mtab)
  ismember=members.has_key(ac_id)
  if not ismember:
    cgiutils.html_end(error="admin account not found.installation error.")
    return
  else:
    index=members.find(ac_id)
    pin=members.data[index]["pin"]
  if int(pinentry) != int(pin):
    cgiutils.html_end(error="Incorrect PIN entered.")
    return
  # which submit button was pressed ?
  option="none"
  for word in ["add","modify","inactive","active","delete","view"]:
    if cgiutils.has_key(word):
      option=word
      break
  if option=="none":
    cgiutils.html_end(error="Invalid submit button value.")
    return
  # If we've got this far, there should either be a valid option and PIN OK
  if option == "add": # need details for new account
    if not cgiutils.has_required(["user_name","email","start_bal"]):
      cgiutils.html_end(error="Missing user_name, email or starting balance.")
      return
    # validate fields
    email=cgiutils.firstval("email")
    if not cgiutils.is_email(email):
      cgiutils.html_end(error="Invalid email address.")
      return
    user_name=cgiutils.firstval("user_name")
    if not cgiutils.is_valid(user_name,max_leng=60,
        allowed='^[A-Za-z][\w\'\- ]+$'):
      cgiutils.html_end(error="Invalid name.")
      return
    # check account doesn't exist
    if members.has_key(user_ac_id):
      cgiutils.html_end(error="Account number/id exists. Can't add account.")
      return
    sbal=cgiutils.stof("start_bal")
    if type(sbal) == type(None): # wasn't valid float
      cgiutils.html_end(error="Invalid starting balance.")
      return
    if sbal > 1000000.0 or sbal < -1000000.0: # unreasonable balance
      cgiutils.html_end(error="starting balance too high or low.")
      return
    # if still here, generate new PIN, create and add row to members
    # and balances tables
    newpin=cgiutils.make_pin()
    row={}
    row["ac_id"]=user_ac_id
    row["name"]=user_name
    row["email"]=email
    row["pin"]=newpin
    row["active"]='Y'
    members.addrow(row)
    brow={}
    brow["ac_id"]=user_ac_id
    brow["balance"]=sbal
    brow["cfwd"]=sbal
    brow["in"]=0.0
    brow["out"]=0.0
    brow["turnover"]=0.0
    balance=tablcgi.table(btab)
    balance.addrow(brow) 
    print "<p>new member added"
    cgiutils.html_end(received=1)
    return
  elif option == "modify": # modify details for account
    modifications=0 # counts number of fields changed
    # check account does exist
    if not members.has_key(user_ac_id):
      error="Account id/no. doesn't exist. Can't modify."
      cgiutils.html_end(error)
      return
    mindex=members.find(user_ac_id)
    balance=tablcgi.table(btab)
    bindex=balance.find(user_ac_id)
    # check email address
    if cgiutils.has_key("email"):
      # validate field
      email=cgiutils.firstval("email")
      if not cgiutils.is_email(email):
        cgiutils.html_end(error="Invalid email address.")
        return
      members.data[mindex]["email"]=email
      modifications+=1
    # check account name 
    if cgiutils.has_key("user_name"):
      # validate field
      user_name=cgiutils.firstval("user_name")
      if not cgiutils.is_valid(user_name,max_leng=60,
          allowed='^[A-Za-z][\w\'\- ]+$'):
        cgiutils.html_end(error="Invalid name.")
        return
      members.data[mindex]["name"]=user_name
      modifications+=1
    if modifications: # save changes to members table if any 
      members.save()
    # check CFWD or start balance 
    if cgiutils.has_key("start_bal"):
      # validate field
      sbal=cgiutils.stof("start_bal")
      if type(sbal) == type(None): # wasn't valid float
        cgiutils.html_end(error="Invalid starting balance.")
        return
      if sbal > 1000000.0 or sbal < -1000000.0: # unreasonable balance
        cgiutils.html_end(error="starting balance too high or low.")
        return
      balance=tablcgi.table(btab)
      old_cfwd=balance.data[bindex]["cfwd"]
      difference=sbal-old_cfwd
      balance.data[bindex]["cfwd"]=sbal
      balance.data[bindex]["balance"]+=difference
      balance.save()
      modifications+=1
    if not modifications: # all changeable fields were blank ?
      cgiutils.html_end(error="No modified field values submitted.")
      return
    else: 
      print "<p> %d field/s modified.</p>" % modifications
      cgiutils.html_end(received=1)
      return
  elif option == "inactive":
    # check account does exist
    if not members.has_key(user_ac_id):
      error="Account id/no. doesn't exist. Can't make inactive."
      cgiutils.html_end(error)
      return
    mindex=members.find(user_ac_id)
    members.data[mindex]["active"]='N'
    members.save()
    cgiutils.html_end(received=1)
    return
  elif option == "active":
    # check account does exist
    if not members.has_key(user_ac_id):
      error="Account id/no. doesn't exist. Can't reactivate."
      cgiutils.html_end(error)
      return
    mindex=members.find(user_ac_id)
    members.data[mindex]["active"]='Y'
    members.save()
    cgiutils.html_end(received=1)
    return
  elif option == "delete":
    if not members.has_key(user_ac_id):
      error="Account id/no. doesn't exist. Can't delete."
      cgiutils.html_end(error)
      return
    mindex=members.find(user_ac_id)
    balance=tablcgi.table(btab)
    if not balance.has_key(user_ac_id):
      error="""Account id/no. has member record but no balance record.
        please inform webmaster."""
      cgiutils.html_end(error)
      return
    bindex=balance.find(user_ac_id)
    bal=balance.data[bindex]["balance"]
    if bal > 0.001 or bal < -0.001:
      error="Account has non-zero balance. Unwise to delete it. Clear it first."
      cgiutils.html_end(error)
      return
    balance.delrow(user_ac_id)
    members.delrow(user_ac_id)
    cgiutils.html_end(received=1)
    return
  elif option == "view":
    if not members.has_key(user_ac_id):
      error="Account id/no. doesn't exist. Can't view it."
      cgiutils.html_end(error)
      return
    mindex=members.find(user_ac_id)
    balance=tablcgi.table(btab)
    if not balance.has_key(user_ac_id):
      error="""Account id/no. has member record but no balance record.
        please inform webmaster."""
      cgiutils.html_end(error)
      return
    bindex=balance.find(user_ac_id)
    bal=balance.data[bindex]["balance"]
    # create members table view object
    mtabvo=tablcgi.table_def(mtab)
    mtabvo.file=None
    mtabvo.meta["keys"].append("cfwd")
    mtabvo.meta["keys"].append("balance")
    mtabvo.meta["keys"].append("in")
    mtabvo.meta["keys"].append("out")
    mtabvo.meta["keys"].append("turnover")
    mtabvo.meta["colheads"].append("CFWD")
    mtabvo.meta["colheads"].append("Balance")
    mtabvo.meta["colheads"].append("In")
    mtabvo.meta["colheads"].append("Out")
    mtabvo.meta["colheads"].append("Turnover")
    mtabvo.meta["formats"].append("%.2f")
    mtabvo.meta["formats"].append("%.2f")
    mtabvo.meta["formats"].append("%.2f")
    mtabvo.meta["formats"].append("%.2f")
    mtabvo.meta["formats"].append("%.2f")
    mtv=tablcgi.table(mtabvo)
    row={}
    for key in ["ac_id","pin","name","email","active"]:
      row[key]=members.data[mindex][key]
    for key in ["cfwd","balance","in","out","turnover"]:
      row[key]=balance.data[bindex][key]
    mtv.addrow(row)
    mtv.tab2html()
    cgiutils.html_end(received=1)
    return

if __name__ == "__main__":
  try:
      main()
  except:
    import traceback
    print "error detected in admin.cgi main()"
    traceback.print_exc()

