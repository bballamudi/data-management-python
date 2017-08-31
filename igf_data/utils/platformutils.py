from igf_data.igfdb.platformadaptor import PlatformAdaptor
from igf_data.utils.dbutils import read_dbconf_json, read_json_data

def load_new_platform_data(data, dbconfig):
  '''
  A method for loading new data for pipeline table
  '''
  try:
    formatted_data=read_json_data(data)
    dbparam=read_dbconf_json(dbconfig)
    pl=PlatformAdaptor(**{dbparam})
    pl.start_session()
    pl.store_platform_data(data=formatted_data)
    pl.close_session()
  except:
    raise

