#!/usr/local/bin/python
# change top line to the path of the Python interpreter on your system

""" balance.cgi This file handles input from the balance 
    form used to request balance details. 
    Richard Kay last changed: 23 Aug 2002
"""

# uncomment next 3 lines to debug script
#import sys
#sys.stderr=sys.stdout
#print "Content-type: text/plain\n"

import cgiutils
import tablcgi
from table_details import btab,mtab

def main():
  cgiutils.html_header(title="LETS Accounting balance request")
  if len(cgiutils.keys()) == 0:
    # if no keys authentication data missing
    cgiutils.html_end(error="Missing authentication details.")
    return
  elif not cgiutils.has_required(["ac_id","pin","enquiry_id"]):
    cgiutils.html_end(error="Missing value/s. Complete all form fields.")
    return

  # check if has required keys and of correct format 
  ac_id=cgiutils.firstval("ac_id")
  pinentry=cgiutils.firstval("pin")
  enquiry_id=cgiutils.firstval("enquiry_id")
  # check field formats 
  if not cgiutils.is_valid(ac_id,max_leng=8,allowed='^[\w]+$'):
    cgiutils.html_end(error="Invalid user account id/no.")
    return
  if not cgiutils.is_valid(enquiry_id,max_leng=8,allowed='^[\w]+$'):
    cgiutils.html_end(error="Invalid enquiry account id/no.")
    return
  if not cgiutils.is_valid(pinentry,allowed='^[1-9][0-9]{3,3}$'):
    cgiutils.html_end(error="Invalid PIN format.")
    return

  # check pin 
  members=tablcgi.table(mtab)
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
  enq_member=members.has_key(enquiry_id)
  if not enq_member:
    cgiutils.html_end(error="Enquiry Account no./id not found.")
    return
  balance=tablcgi.table(btab)
  if not balance.has_key(enquiry_id):
    error="""enquiry a/c has member record but no balance record. 
      please inform webmaster."""
    cgiutils.html_end(error)
    return
  # display details
  bindex=balance.find(enquiry_id)
  bal=balance.data[bindex]["balance"]
  # create balance table view object
  bvd=tablcgi.table_def(btab)
  bvd.file=None
  btv=tablcgi.table(bvd)
  row={}
  for key in ["ac_id","cfwd","balance","in","out","turnover"]:
    row[key]=balance.data[bindex][key]
  btv.addrow(row)
  btv.tab2html()
  cgiutils.html_end(received=1)
  return 

if __name__ == "__main__":
  try: 
    main()
  except:
    import traceback
    print "error detected in balance.cgi main()"
    traceback.print_exc()

