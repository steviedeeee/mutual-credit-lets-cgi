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
    errormes="could not get exclusive lock on next ackid file")
    raise errormes 
  return nextnum

