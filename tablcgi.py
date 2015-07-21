"""tablcgi.py
   Classes to provide support for simple database tables for
   MRS and CGI applications with semi-persistent data.

   To make this data persistent, file locking is provided,
   by using the LockFile module copied from MailMan Python 
   source code, see www.list.org .

   table_def class is used to create multiple table definition
   objects based on independent (cloned) data so that more than
   one table of a particular kind can be opened at the
   same time without cross referring to (and messing with) each 
   others attribute values, e.g. filename.

   table class contains methods to load, save, print as HTML,
   and to find, add, remove and modify rows. Objects store a 
   list of dictionaries, each dictionary is one row. Objects also
   store meta data, used to control column operations,
   and the filename in which the updated object is 
   saved as a pickle file. 

   See tester() code for usage examples.
   and read the source code for the full documentation.
   
   Distributed under the terms of the GNU Public License, 
   version 2 or higher, see http://www.gnu.org/ for details.

   This program comes without warranty of any kind.

   Richard Kay, 26/04/02"""


ColumnException="column error" # incorrectly coded column value
                               # in application using the table class

RowException="row error" # attempt to add existing row, or delete
                         # or modify non existing row etc.

class update_set:
  ''' builds a list of code references and parameters for updates which
  are to be grouped together. dispatch method executes these
  all in one go. 

  TBD - make what this does fully atomic with a rollback if it doesn't 
  complete and a commit if it does.  Possible
  way forward is store an object which for each atomic update set:
  a. backs up all data to be modified/removed.
  b. monitors status of transaction - this needs to be carried
  out prior to starting any update to check all resources are 
  ready, periodically and on system startup to check for and either 
  roll back or clean up any committed but incomplete transactions.
  c. says what its going to do, with new data.
  d. records status: Preparation -> Processing -> Commit -> Complete
  
  Preparation includes taking backups, locking all resources.
  Processing means updating the target files and flushing to disk.
  Commit means passing point of no return, removing locks and cleaning 
  up rollback resources.
  Complete means everything cleaned up.

  Rollback is what happens when monitoring detects an update having
  entered the processing state and having crashed or hung prior to 
  commit.
  '''

  def __init__(self,logging=0,logfile='MRS_update_together.log'):
    ''' initialises an update_set object '''
    self.logfile=logfile
    self.logging=logging
    self.exec_list=[]
    if self.logging: 
      self.lfp=open(logfile,'a')
  def add_entry(self,coderef,params):
    ''' takes code reference and parameters and adds entry to
    the execution list'''
    entry={'coderef':coderef,'params':params}
    self.exec_list.append(entry)
    if self.logging: 
      self.lfp.write('update_together.add_entry: '+ repr(entry)+'\n')
  def dispatch(self):
    ''' executes all entries in the execution list in one go.'''
    for entry in self.exec_list:
      if self.logging: 
        self.lfp.write('update_together.dispatch: '+ repr(entry)+'\n')
      apply(entry['coderef'],entry['params'])


class table_def:
  ''' clones a specialised table_def object based on a table_def class
  in other modules, allowing multiple table definitions derived from 
  the same original to coexist without clobbering each others attributes.
  This is achieved using the [:] full slice operator, which does a
  full copy of a list-type item (string,list,or tuple). This approach 
  doesn't just provide another reference to the same object. A new 
  meta-data dictionary is built from scratch using cloned strings.'''
  def __init__(self,defobj):
    if defobj.file: 
      self.file=defobj.file[:] # use full slice to clone string
    else:
      self.file=None
    self.index_col=defobj.index_col[:]
    self.meta={}
    for key in defobj.meta.keys():
      selfkey=key[:] # clone key
      self.meta[selfkey]=defobj.meta[key][:] # clone list indexed by key

class table:
  """ class which stores a table using a pickle file and do
  add/mod/del row operations on the table. table data is a list of
  dictionaries each dictionary is for a row. meta data is a dictionary 
  of lists each list holding ordered information about columns for
  display purposes """
  def __init__(self,defin,dir=None,read_locked=0):
    # table defin(ition) has attributes meta,file,index_col
    # if read_locked == 1 the table will be locked prior to
    # opening in order to maintain the lock for the duration of
    # table object open->read->close->open->write->close cycle
    # which may be required to prevent concurrent updates between 
    # connected read and write operations on same table object.
    # 
    # if self.filename has value None, the table is a view and is neither
    # loaded from nor saved to a file. 
    # 
    # in order to prevent unwanted manipulation of attributes through
    # the defin parameter object, first clone it.
    self.defin=table_def(defin)
    self.meta=self.defin.meta
    # meta is information about data, is a set of lists in matching order.
    # each element of a list is information about a column (col) in data.
    # meta["keys"] = list of keys in the column order of printing
    # meta["colheads"] = column headings for printing
    # meta["formats"] = print formats e.g. '%.2f', '%s', '%d'
    # 
    # dir allows multiple instances of the table in different
    # directories. dir is the directory prefix of the file.
    if dir and self.file:
      import os
      self.file=os.path.join(dir,self.defin.file)
      self.lockfilename=self.file+'.lock'
    elif defin.file:
      self.file=self.defin.file
      self.lockfilename=self.file+'.lock'
    else:
      self.file=None
      self.lockfilename=None
    # file is where the filename data is loaded from and saved to
    self.read_locked=read_locked
    self.index_col=self.defin.index_col
    if not self.index_col in self.meta["keys"]:
      raise ColumnException
    # index_col is the column used to index data
    # data is a list of dictionaries saved in filename
    self.data=self.load()
  
  def load(self): # loads data from file, or empty list
    """ loads serialised data object from pickle file """
    import pickle, LockFile
    if not self.file:
      return [] # a memory constructed view is neither loaded nor saved
    if self.read_locked: 
      self.lock=LockFile.LockFile(self.lockfilename,withlogging=1)
    try:
      if self.read_locked: 
        try:
          self.lock.lock(15)
        except LockFile.LockError:
          self.lock.unlock()
          raise LockFile.LockError
      fp=open(self.file,"r")
      data=pickle.load(fp)
      fp.close()
      return data
    except(IOError): # at start no rows in table
      return []
  
  def save(self):
    """ saves structured object into pickle file. Uses Mailman 
    LockFile() module. returns 1 if update successful, otherwise 0.
    When adding or deleting a row there is no need to lock
    before reading data. However, when modifying a row, in
    order to prevent race conditions between processes updating
    different columns in the same row, it is neccessary
    to lock the row before current contents are read, so that
    updates which have occurred between the current processes' 
    read and write operations are not overridden. 
    """
    import pickle
    import LockFile
    if not self.file:
      return 0 # a memory constructed view is neither loaded nor saved
    if not self.read_locked: 
      self.lock=LockFile.LockFile(self.lockfilename,withlogging=1)
    try:
      try:
        if not self.read_locked: 
          self.lock.lock(15)
        fp=open(self.file,"w")
        pickle.dump(self.data,fp)
        fp.flush()
        fp.flush()
        fp.close()
      finally:   
        self.lock.unlock()
    except LockFile.LockError:
      return 0 # didn't update stored table
    else:
      return 1 # did update stored table
  
  def find(self,value):
    """ returns index of 1st record whose index_col equals value 
        or returns -1"""
    if not self.index_col in self.meta["keys"]:
      raise ColumnException
    i=0
    for rec in self.data:
      if rec[self.index_col] == value:
        return i
      i+=1
    return -1 # value not present in column
  
  def has_key(self,value):
    """ returns 1 if value present within index column or 0 """
    if self.find(value) == -1:
      return 0
    else:
      return 1

  def keys(self):
    """ returns index column as a list """
    if not self.index_col in self.meta["keys"]:
      raise ColumnException
    keylist=[]
    for rec in self.data:
       keylist.append(rec[self.index_col])
    return keylist
  
  def addrow(self,row):
    """ adds row which must be
        validated before calling this method.  """
    keys=self.meta["keys"][:] # need a copy of keys list, not another
    # reference to it or sort will put meta["keys"] into wrong order !!
    rowkeys=row.keys()
    keys.sort()
    rowkeys.sort()
    if ((not keys == rowkeys) or 
        (self.index_col and not self.index_col in keys)):
      raise ColumnException
    if self.index_col:
      atrow=self.find(row[self.index_col])
      if atrow != -1:
        raise RowException 
    self.data.append(row) # add row at end of data
    return self.save()
  
  def modrow(self,row):
    ''' Re-reads data and modifies fields present in
    row before saving. Leaves fields not present in row
    unchanged.
    Parameters: 
    row - dictionary containing unique column plus 1 or more 
      key/value sets of field updates for row to be modified. Must 
      include unique column value for row to be updated, and fields
      to be modified. row must not include fields to be left alone.
    '''
    
    # first do some sanity checking
    if type(row) != type({}):
      raise TypeError
    if not row.has_key(self.index_col):
      raise ColumnException
    row_key=row[self.index_col]
    row_index=self.find(row_key)
    if row_index == -1:
      raise RowException # cant mod row that doesn't exist
    for key in row.keys():
      if key not in self.meta['keys']: # extraneous key
        raise ColumnException 
      if key != self.index_col:
        self.data[row_index][key]=row[key]
    return self.save()
  
  def delrow(self,value):
    """ deletes row. index_col required and row with same column value must
        already exist or row will not be deleted """
    keys=self.meta["keys"]
    if not self.index_col in keys:
      raise ColumnException
    atrow=self.find(value)
    if atrow == -1:
      raise RowException # cant del row that doesn't exist
    del self.data[atrow] # remove row whose col == value
    return self.save()

  def tab2html(self,skip_cols=[],align='center',bgcolor='#ffffff',border=2):
    """ prints data as a HTML table using meta data for formatting """
    print "<p>"
    print """<table align="%s" 
                    bgcolor="%s" 
                    border=%d >""" % (align,bgcolor,border)
    # print column headings
    print "<tr>"
    i=0
    for heading in self.meta["colheads"]:
      key=self.meta["keys"][i]
      if key not in skip_cols: 
        print "<th> %s </th>" % heading
      i+=1
    print "</tr>"
    # loop through rows
    for row in self.data:
      print "<tr>"
      # loop through cols
      i=0      
      for key in self.meta["keys"]:
        # format object can be a printf conversion e.g. "%.2f" or
        # it could be a code reference or None
        format_obj=self.meta["formats"][i]
        is_string=0 
        is_code=0
        def dummy_code_obj(): pass # dummy code object for code type
        if type(format_obj) == type(""):
          is_string=1 
          formatstr="<td> %s </td>" %  format_obj
        elif type(format_obj) == type(dummy_code_obj):
          is_code=1
        # substitute %s|%f|%d type format conversion
        if key not in skip_cols and is_string:
          print formatstr % row[key] # substitute value
        elif key not in skip_cols and is_code:
          print "<td> ",
          format_obj(row[key]) # call code object to print value
          print "</td> "
        i+=1
      print "</tr>"
    print "</table>"
    print "</p><br>"

def tester():
  """ Runs tests on table class. Each use of the menu is intended to
      create valid HTML output which can be cut/pasted/saved using 
      an HTML source editor e.g. Quanta plus. HTML validation/viewing 
      can be done using HTML development environment. The table class
      will create a pickle file: temp.pkl and use this to store data 
      between program runs. """
  def hash_mark(mark):
    # demonstrates use of passed code as formatting object
    print "## %.1f ##" % mark,
  
  class tabledefinition:
    pass 
  defin=tabledefinition()
  # meta data for test table
  defin.meta={"keys":["snum","name","mark"],
        "colheads":["Student No.","Name","Mark"],
        "formats":["%s","%s",hash_mark]}
  defin.index_col="snum"
  defin.file="temp.pkl"
  recs=[{"snum":"12345670","name":"Peter Smith"   ,"mark":45.2},
        {"snum":"01234567","name":"Wu Chan"       ,"mark":68.7},
        {"snum":"80123456","name":"Siobhan Murphy","mark":59.2}]
 
  readlock=int(raw_input('enter 1 for read/write locking or 0 write locking'))
  while 1: 
    # cgiutils2.html_header(bgcolor='"#ffff88"')
    # instantiate table object with no records (first time round)
    print "<pre>" # menu works interactively and in a html
    print "enter   to test"
    print "  1     add record"
    print "  2     modify record"
    print "  3     delete record"
    print "  4     show table as HTML"
    print "  5     Quit"
    test=int(raw_input("option: "))
    print "</pre>"
    if test == 1:
      recno=int(raw_input("which record to add (0-2): "))
      tbl=table(defin,read_locked=readlock)
      tbl.addrow(recs[recno]) 
      # cgiutils2.html_end()
    elif test == 2:
      recno=int(raw_input("which record to change (0-2): "))
      mark=float(raw_input("enter new mark (0.0-100.0): "))
      recs[recno]["mark"]=mark
      tbl=table(defin,read_locked=readlock)
      tbl.modrow(recs[recno])
      # cgiutils2.html_end()
    elif test == 3:
      recno=int(raw_input("which record to delete (0-2): "))
      tbl=table(defin,read_locked=readlock)
      tbl.delrow(recs[recno]["snum"])
      # cgiutils2.html_end()
    elif test == 4:
      tbl=table(defin) # don't lock if only reading not writing
      tbl.tab2html()
      # cgiutils2.html_end()
    elif test == 5:
      # cgiutils2.html_end()
      break
  
if __name__ == "__main__": # unit test condition
  tester()
