import shutil,os, subprocess,json
import pandas as pd
from shlex import quote

def get_storage_stats_in_gb(storage_list):
  '''
  A utility function for fetching disk usage stats (df -h) and return disk
  usge in Gb

  :param storage_list, a input list of storage path

  returns a list of dictionary containing following keys
     storage
     used
     available
  '''
  try:
    storage_stats=list()
    for storage_path in storage_list:
      if not os.path.exists(storage_path):
        raise IOError('path {0} not found'.format(storage_path))
      else:
        storage_usage=shutil.disk_usage(storage_path)
        storage_stats.append({'storage':storage_path,
                              'used':storage_usage.used/1024/1024/1024,
                              'available':storage_usage.free/1024/1024/1024})
    return storage_stats
  except:
    raise

def merge_storage_stats_json(config_file,label_file=None,
                             server_name_col='server_name',
                             storage_col='storage',
                             used_col='used',
                             available_col='available',
                             disk_usage_col='disk_usage'
                             ):
  '''
  A utility function for merging multiple disk usage stats file generated by
  json dump of get_storage_stats_in_gb output
  
  :param config_file, a disk usage status config json file with following keys
           server_name
           disk_usage
         Each of the disk usage json files should have following keys
           storage
           used
           available 
  :param label_file, an optional json file for renaming the raw disk names
         format: <raw name> : <print name>
  
  returns 
    * merged data as a list of dictionaries
    * a dictionary containing the description for the gviz_data
    * a list of column order
  '''
  try:
    with open(config_file,'r') as j_data:
      server_config=json.load(j_data)                                           # read the disk usage config file

    all_storage_info=pd.DataFrame([{}],\
                                  columns=[server_name_col,
                                           storage_col,
                                           used_col,
                                           available_col])                      # an empty data frame for merged data
    for server_info in server_config:
      if not os.path.exists(server_info[disk_usage_col]):
        raise IOError('Missing file {0}'.format(server_info[disk_usage_col]))

      data=pd.read_json(server_info[disk_usage_col])
      data[server_name_col]=server_info[server_name_col]
      data[storage_col]=data[server_name_col] + '_' + data[storage_col]         # add server name as the storage name prefix
      all_storage_info=pd.concat([all_storage_info,data])                       # merge disk usage info

    all_storage_info[pd.isna(all_storage_info[server_name_col])==False]         # remove entries without server name col
    all_storage_info.drop(server_name_col,inplace=True,axis=1)                  # remove server name column from merged data
    all_storage_info=all_storage_info.\
                     set_index(storage_col).\
                     reset_index(storage_col)                                   # fix dataframe index issue
    all_storage_info[used_col]=all_storage_info[used_col].\
                               astype(float)                                    # convert used column to float
    all_storage_info[available_col]=all_storage_info[available_col].\
                                    astype(float)                               # convert available column to float
    if label_file:
      with open(label_file,'r') as j_data:
        storage_label=json.load(j_data)                                         # load data for storage name label

      all_storage_info[storage_col]=all_storage_info[storage_col].\
                                    map(storage_label)                          # change storage names in data frame

    desctiption={ storage_col: ("string", "Server Name"),
                  used_col: ("number","Used space (in Gb)"),
                  available_col:("number","Available space (in Gb)"),
                }                                                               # create description dictionary for gviz_api
    column_order=[storage_col,used_col,available_col]                           # create column order for gviz_api
    return all_storage_info.to_dict(orient='records'), desctiption, column_order
  except:
    raise

def get_sub_directory_size_in_gb(input_path,dir_name_col='directory_name',
                                 dir_size_col='directory_size'):
  '''
  A utility function for listing disk size of all sub-directories for a given path
  (similar to linux command du -sh /path/* )

  :param input_path, a input file path
  :param dir_name_col, column name for directory name, default directory_name
  :param dir_size_col, column name for directory size, default directory size
  returns the following
    * a list of dictionaries containing following keys
        directory_name
        directory_size
    * a description dictionary for gviz_api
    * a column order list for gviz _api
  '''
  try:
    storage_stats=list()
    for dir_name in os.listdir(input_path):
      cmd=['du','-s',quote(os.path.join(input_path,dir_name))]
      proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
      proc.wait()
      outs,_=proc.communicate()
      if proc.returncode == 0:
        dir_size,dir_name=outs.decode('utf-8').split()
        storage_stats.append({dir_name_col:os.path.basename(dir_name),
                              dir_size_col:int(dir_size)/1024/1024/1024})
      else:
        raise ValueError('Failed directory size check: {0}'.format(err))

    storage_stats=pd.DataFrame(storage_stats)                                   # convert to dataframe
    storage_stats[dir_size_col]=storage_stats[dir_size_col].astype(float)       # change column type to float
    storage_stats.sort_value(by=[dir_size_col],ascending=False,inplace=True)    # sort dataframe by dir size
    storage_stats=storage_stats.to_dict(orient='record')                        # convert to list of dictionary
    description={dir_name_col: ("string", "Project Name"),
                 dir_size_col: ("number","Size (in GB)"),
                }                                                               # a description for gviz_api
    column_order=[dir_name_col,dir_size_col]                                    # a column order for gviz_api
    return storage_stats, description, column_order
  except:
    raise