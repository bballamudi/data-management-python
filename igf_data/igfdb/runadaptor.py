import json
import pandas as pd
from sqlalchemy.sql import table, column
from igf_data.igfdb.baseadaptor import BaseAdaptor
from igf_data.igfdb.igfTables import Experiment, Run, Run_attribute, Seqrun

class RunAdaptor(BaseAdaptor):
  '''
   An adaptor class for Run and Run_attribute tables
  '''

  def store_run_and_attribute_data(self, data, autosave=True):
    '''
    A method for dividing and storing data to run and attribute table
    '''
    (run_data, run_attr_data)=self.divide_data_to_table_and_attribute(data=data)

    try:
      self.store_run_data(data=run_data)                                                   # store run
      if len(run_attr_data.columns)>0:                                                     # check if any attribute exists
        self.store_run_attributes(data=run_attr_data)                                      # store run attributes
      if autosave:
        self.commit_session()                                                              # save changes to database
    except:
      if autosave:
        self.rollback_session()
      raise


  def divide_data_to_table_and_attribute(self, data, required_column='run_igf_id', attribute_name_column='attribute_name', attribute_value_column='attribute_value'):
    '''
    A method for separating data for Run and Run_attribute tables
    required params:
    required_column: column name to add to the attribute data
    attribute_name_column: label for attribute name column
    attribute_value_column: label for attribute value column

    It returns two pandas dataframes, one for Run and another for Run_attribute table

    '''
    if not isinstance(data, pd.DataFrame):
      data=pd.DataFrame(data)

    run_columns=self.get_table_columns(table_name=Run, excluded_columns=['run_id', 'seqrun_id', 'experiment_id'])     # get required columns for run table
    run_columns.extend(['seqrun_igf_id', 'experiment_igf_id'])
    (run_df, run_attr_df)=BaseAdaptor.divide_data_to_table_and_attribute(self, \
                                                      data=data, \
    	                                              required_column=required_column, \
    	                                              table_columns=run_columns,  \
                                                      attribute_name_column=attribute_name_column, \
                                                      attribute_value_column=attribute_value_column \
                                                    )                                                                 # divide data to run and attribute table
    return (run_df, run_attr_df)
   

  def store_run_data(self, data, autosave=False):
    '''
    Load data to Run table
    '''
    try:
      if not isinstance(data, pd.DataFrame):
        data=pd.DataFrame(data)

      if 'seqrun_igf_id' in data.columns:
        seqrun_map_function=lambda x: self.map_foreign_table_and_store_attribute( \
                                               data=x, \
                                               lookup_table=Seqrun, \
                                               lookup_column_name='seqrun_igf_id', \
                                               target_column_name='seqrun_id')             # prepare seqrun mapping function
        new_data=data.apply(seqrun_map_function, axis=1)                                   # map seqrun id
        data=new_data                                                                      # overwrite data

      if 'experiment_igf_id' in data.columns:
        exp_map_function=lambda x: self.map_foreign_table_and_store_attribute(\
                                               data=x, \
                                               lookup_table=Experiment, \
                                               lookup_column_name='experiment_igf_id', \
                                               target_column_name='experiment_id')          # prepare experiment mapping function
        new_data=data.apply(exp_map_function, axis=1)                                       # map experiment id
        data=new_data                                                                       # overwrite data

      self.store_records(table=Run, data=data)                                              # store without autocommit
      if autosave:
        self.commit_session()
    except:
      if autosave:
        self.rollback_session()
      raise


  def store_run_attributes(self, data, run_id='', autosave=False):
    '''
    A method for storing data to Run_attribute table
    '''
    try:
      if not isinstance(data, pd.DataFrame):
        data=pd.DataFrame(data)                                                             # convert data to dataframe

      if 'run_igf_id' in data.columns:
        run_map_function=lambda x: self.map_foreign_table_and_store_attribute(\
                                               data=x, \
                                               lookup_table=Run, \
                                               lookup_column_name='run_igf_id', \
                                               target_column_name='run_id')                 # prepare run mapping function
        new_data=data.apply(run_map_function, axis=1)
        data=new_data                                                                       # overwrite data    

      self.store_attributes(attribute_table=Run_attribute, linked_column='run_id', db_id=run_id, data=data) # store without autocommit
      if autosave:
        self.commit_session()
    except:
      if autosave:
        self.rollback_session()
      raise


  def fetch_run_records_igf_id(self, run_igf_id, target_column_name='run_igf_id'):
    '''
    A method for fetching data for Run table
    required params:
    run_igf_id: an igf id
    target_column_name: a column name, default run_igf_id
    '''
    try:
      column=[column for column in Run.__table__.columns \
                       if column.key == target_column_name][0]
      run=self.fetch_records_by_column(table=Run, \
      	                                   column_name=column, \
      	                                   column_id=run_igf_id, \
      	                                   output_mode='one')
      return run  
    except:
      raise


