#!/usr/bin/python

# script to start a LETS CGI database clean with just an
# admin account and next_ackid = 1

# change next line to your accounting administration email address
admin_email='covlets-admin@copsewood.net'
import tablcgi,cgiutils
import os,os.path,pickle
from table_details import mtab,naid
# get rid of unwanted files
for filename in ['summary_all.pkl','summary_active.pkl',"members.pkl",
    "balances.pkl","acks.pkl","turnover.pkl","next_ackid.pkl"]:
  if os.path.isfile(filename):
    os.unlink(filename)

# create members file with admin a/c
pin=cgiutils.make_pin()
print "PIN for admin account is: ",pin
members=tablcgi.table(mtab)
mrow={"ac_id":'admin',
      "pin":pin,
      "name":"Online Account Administrator",
      "email":admin_email,
      "active":'Y'}
members.addrow(mrow)

# place next ackid (1) into next_ackid file
fp=open(naid.file,"w")
pickle.dump(1,fp)
fp.close()

