# table_details.py: details of tables used within LETS CGI 
# simple accounts management system. These details are coded 
# in this file and imported into programs which access
# tables, enabling common details to edited in one place.

# trivial table definitions class used to simplify naming
class table_def:
  pass

# data for members table
mtab=table_def()
mtab.meta={
  "keys":["ac_id","pin","name","email","active"],
  "colheads":["A/C","PIN","Name","email","Active"],
  "formats":["%s","%s","%s","%s","%s"]}
mtab.file="members.pkl"
mtab.index_col="ac_id"

# data for balances table 
btab=table_def()
btab.meta={
  "keys":["ac_id","cfwd","balance","in","out","turnover"],
  "colheads":["A/C","CFWD","Balance","In","Out","Turnover"],
  "formats":["%s","%.2f","%.2f","%.2f","%.2f","%.2f"]}
btab.file="balances.pkl"
btab.index_col="ac_id"

# data/code for acknowledgements table
def print_date_time(timeval):
  import time
  time_struct=time.localtime(timeval)
  print time.asctime(time_struct)

atab=table_def()
atab.meta={
  "keys":["ack_id","from_id","from_name","to_id","to_name","system",
  "amount","details","time"],
  "colheads":["ack_id","from_A/C","from_name","to_A/C","to_name","System",
  "Amount","Details","Date/Time Recorded"],
  "formats":["%s","%s","%s","%s","%s","%s","%.2f","%s",print_date_time]}
atab.file="acks.pkl"
atab.index_col="ack_id"

# data for summary table
stab=table_def()
stab.meta={
  "keys":["ac_id","name","cfwd","balance","in","out","turnover"],
  "colheads":["A/C","Name","CFWD","Balance","In","Out","Turnover"],
  "formats":["%s","%s","%.2f","%.2f","%.2f","%.2f","%.2f"]}
stab.file="turnover.pkl"
stab.index_col="ac_id"

# next ackid file
naid=table_def()
naid.file="next_ackid.pkl"
