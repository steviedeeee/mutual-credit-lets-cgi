""" cgiutils2.py
    Richard Kay, 16 April 2002
    Collects various CGI programming utilities into one place 

    version 2 adds cgi form field input capabilities.

Copyright (C) 2002 Richard Kay 
Email: Richard.Kay@tic.ac.uk

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, this is available from 
http://www.gnu.org/licenses/gpl.html or by writing to the Free 
Software Foundation, Inc., 59 Temple Place - Suite 330, 
Boston, MA  02111-1307, USA.  """

import cgi
form = cgi.FieldStorage()

def make_pin(min=1000,max=9999):
  """ generates a random PIN number used for user authentication or
  session tracking. """
  import random
  return random.randrange(1000,9999)

def keys():
  """ shortcut to form.keys() method """
  return form.keys()

def has_key(key):
  """ shortcut to form.has_keys() method """
  return form.has_key(key)

def has_required(required):
  """ checks if required keys are present in form.getvalue
  user must supply required as a list of key names, e.g.
  if not has_required(["Email","Name"]):
    cgiutils2.html_end(error="You havn't input all required values")
  """
  formkeys=keys()
  for key in required:
    if not key in formkeys:
      return 0 # not all required keys present in form
  return 1 # all required keys present in form

def firstval(key,default=""):
  """ returns value from form as a single string, or default for 
  empty/wrong type. Returns first of a multi-valued submission. """
  value=form.getvalue(key)
  if type(value) == type([]): # multi value submission
    if value == []: # empty list ??
      return default 
    elif type(value[0]) == type(""): # first element is string
      return value[0]
    else: # list, but 1st element not a string 
      return default 
  elif type(value) == type(""):
    return value
  else: # dont know what type of data this is
    return default 

def listval(key,default=[]):
  """ returns val as a list of strings"""
  value=form.getvalue(key)
  strings=[]
  if type(value) == type([]): # multi value submission
    for i in range(len(value)):
      if type(value[i]) == type(""):
        strings.append(value[i])
  elif type(value) == type(""):
    strings.append(value)
  return strings

def stof(key,default=None):
  """ string to float conversion or returns default for non float value"""
  string=firstval(key) # converts to single string or ""
  try:
    f=float(string)
  except:
    return default 
  else:
    return f

def stoi(key,default=None):
  """ string to int conversion or returns default for non int value"""
  string=firstval(key) # converts to single string or ""
  try:
    i=int(string)
  except:
    return default 
  else:
    return i 

def is_valid(data,max_leng=30,allowed=r"^\w+$",prohibited=None):
   """data (string) is valid if <= max_leng,
     AND if an allowed RE is specified:  must match allowed.
     AND must not match a prohibited RE 
     Defaults: max_leng: 30, allowed: string of 1 or more \w word chars"""
   import re
   if len(data) > max_leng:
       return 0 # not valid
   if allowed:
       match_allowed=re.search(allowed,data)
       if not match_allowed:
           return 0 # not valid
   if prohibited: # function can also be used to exclude prohibited RE
       match_prohibited=re.search(prohibited,data)
       if match_prohibited:
           return 0 # not valid
   return 1 # passed all tests so should be valid

def is_email(address):
    """ Checks whether a supplied email address is valid or not. 
      Allowed RE: any word characters , dot (.) and at (@).
      Prohibited RE: any dot or at in the wrong place, 
      or no at or more than 1 at's or less than 1 dot's."""
    return is_valid(address,max_leng=100, 
       allowed=r"^[\w\.@]+$", 
       prohibited=r"^[\.@]|\.@|@\.|\.\.|@.*@|[\.@]$|^[^.]+$|^[^@]+$")

def make_clean(string,prohibited=
    r"[^\w \.\,\;\:\!\$\%\-\+\*\=\#\~\/\!\n\t\?\@\(\)\\]"):
    """ cleans up string by removing prohibited characters defined by a
      regular expression character class """
    import re
    reobj=re.compile(prohibited)
    string=reobj.sub('',string) # remove all prohibited chars 
    return string

def html_header(title="CGI generated HTML",bgcolor='"#FFFFFF"'):
    """ prints HTTP/HTML header to browser  """
    print "Content-type: text/html\n"
    print "<HTML><Head><Title>",title,"</Title></Head>"
    print "<Body bgcolor=",bgcolor,"><H1>",title,"</H1>"

def send_mail(fromaddress,toaddress,message,debug=0):
    """ sends a mail message """
    import smtplib
    server = smtplib.SMTP('localhost') # create server object
    if debug: server.set_debuglevel(1)
    server.sendmail(fromaddress, toaddress, message) # send message
    server.quit() # close mail server connection

def html_end(error="",received=0,want_form=0):
    """ ends an html with error message or assurance. 
     Change homepage reference to your own homepage URL """
    homepage='"http://copsewood.net/"'
    if error: # only happens if this parameter is filled in
        print "<p> ",error,"</p>" # print details of the error
        print "<p>An error has occurred. Please press the &lt;back&gt; "
        print "key on your browser and correct/complete your input</p>"
    elif received: # standard response if valid data received and processed 
        print "<p>Thanks for your input which has been received and "
        print "processed.</p>"
    # useful to give a way out at the end of a dialog or session. 
    if not want_form:
      print "<p>Press the &lt;back&gt; key on your browser to continue."
      print "You can return to our "
      print "<a href=%s>home page</a> if you prefer. " % homepage
    print "</body></html>" # end html

def send_form(html_file,vars=[]):
    """ sends an html form to browser
    Name of file containing standard HTML is in html_file parameter.
    This file may contain %d, %f and %s and other Python string escapes.
    These escapes should match in number, type and sequence with the
    vars[] list of (typically hidden field) values to be interpolated."""
    inp = open(html_file,'r')
    form=inp.read() # read HTML form from html_file
    if vars: 
      tvars=tuple(vars) # convert vars form variables list to tuple
      print form % tvars  # send session coded form to browser
    else:
      print form


def tester():
  """ unit test code for module cgiutils.py """
  while 1:
    print "enter   to test"
    print "  1     data validation"
    print "  2     Send mail message"
    print "  3     Normal HTML"
    print "  4     Error HTML"
    print "  5     Form HTML"
    print "  6     Quit"
    test=int(raw_input("option: "))
    if test == 1:
        data=raw_input("enter data to be validated as a string: ")
        max=int(raw_input("enter max data length as an int: "))
        allowed=raw_input("enter allowed Regular Expression: ")
        prohibited=raw_input("enter prohibited RE or None : ")
	if prohibited == "None": prohibited=None # null object
        if is_valid(data,max,allowed,prohibited):
            print "data is valid"
        else:
            print "invalid data detected"
    elif test == 2:
        message=raw_input("input send_mail() test message: ")    
        toaddress=raw_input("enter to address for test message: ")
        fromaddress=raw_input("enter from address for test message: ")
        if is_email(fromaddress) and is_email(toaddress):
            send_mail(fromaddress,toaddress,message)
            print "message sent"
        else:
            print "one or both addresses were invalid"
    elif test == 3:
        html_header(title="Testing cgiutils normal HTML",bgcolor='"#FFFF88"')
        html_end()
    elif test == 4:
        error=raw_input("input error message") 
        html_header(title="Testing cgiutils error HTML",bgcolor='"#FF88FF"')
        html_end(error)
    elif test == 5:
        # the form facility is more complex to setup, 
        # this requires a custom HTML file and variable data for a
        # secure form driven application. Play around with
        # http://copsewood.net/letsplay to get the general idea of how
        # PIN and ID fields stay associated with a user session,
	# and to register your own ID and PIN which can be used here.
        html_header(title="Testing cgiutils form HTML",bgcolor='"#88FFFF"')
        scratch=raw_input("enter name for temporary scratch file: ")
        id=raw_input("enter value for letsplay ID field: ")
        import random
        pin=int(raw_input("enter (int) letsplay PIN or 0 for a random one: "))
        if not pin: pin=make_pin()
        form="""<form action="http://copsewood.net/cgi-bin/wantsform.pl" 
            method="post">
            <INPUT TYPE="hidden" NAME="id" VALUE="%s" >
            <INPUT TYPE="hidden" NAME="pin" VALUE="%d" >
            <p><b>View Wants</b> :
            <INPUT TYPE=Checkbox NAME="view"><p>
            <INPUT TYPE="submit"></form></body></html>"""
        sfile=open(scratch,"w") # write HTML form to scratch file
        sfile.write(form)
        sfile.close()
        send_form(scratch,vars=[id,pin]) # test send_form function
    elif test == 6:
        break
    else:
        print "invalid option. Try again\n"
    raw_input("press enter to continue testing")

if __name__ == '__main__': # true when run, false when imported
    tester()

