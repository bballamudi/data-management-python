import pandas as pd
from sqlalchemy.sql import column
from igf_data.igfdb.baseadaptor import BaseAdaptor
from igf_data.igfdb.igfTables import Seqrun, Run, Platform, Seqrun_attribute, Seqrun_stats, Flowcell_barcode_rule

class SeqrunAdaptor(BaseAdaptor):
  '''
  An adaptor class for table Seqrun
  '''

  def store_seqrun_and_attribute_data(self, data, autosave=True):
    '''
    A method for dividing and storing data to seqrun and attribute table
    '''
    (seqrun_data, seqrun_attr_data)=self.divide_data_to_table_and_attribute(data=data)

    try:                                                                                 
      self.store_seqrun_data(data=seqrun_data)                                                # store run
      if len(seqrun_attr_data.index)>0:                                                     # check if any attribute exists
        self.store_seqrun_attributes(data=seqrun_attr_data)                                   # store run attributes
     
      if autosave:
        self.commit_session()                                                                 # save changes to database
    except:
      if autosave:
        self.rollback_session()
      raise


  def divide_data_to_table_and_attribute(self, data, required_column='seqrun_igf_id',
                                         table_columns=None,
                                         attribute_name_column='attribute_name',
                                         attribute_value_column='attribute_value'):
    '''
    A method for separating data for Seqrun and Seqrun_attribute tables
    
    :param data: A list of dictionaries or a pandas dataframe
    :param table_columns: List of table column names, default None
    :param required_column: column name to add to the attribute data
    :param attribute_name_column: label for attribute name column
    :param attribute_value_column: label for attribute value column
    :returns: two pandas dataframes, one for Seqrun and another for Run_attribute table
    '''
    if not isinstance(data, pd.DataFrame):
      data=pd.DataFrame(data)

    seqrun_columns=self.get_table_columns(\
                     table_name=Seqrun,
                     excluded_columns=['seqrun_id', 'platform_id'])             # get required columns for run table
    seqrun_columns.extend(['platform_igf_id'])
    (seqrun_df, seqrun_attr_df)=\
      BaseAdaptor.\
        divide_data_to_table_and_attribute(\
          self,
          data=data,
          required_column=required_column,
          table_columns=seqrun_columns,
          attribute_name_column=attribute_name_column,
          attribute_value_column=attribute_value_column
        )                                                                       # divide data to run and attribute table
    return (seqrun_df, seqrun_attr_df)


  def store_seqrun_data(self, data, autosave=False):
    '''
    Load data to Seqrun table
    '''
    try:
      if not isinstance(data, pd.DataFrame):
        data=pd.DataFrame(data)

      if 'platform_igf_id' in data.columns:
        platform_map_function=lambda x: self.map_foreign_table_and_store_attribute( \
                                                data=x, \
                                                lookup_table=Platform, \
                                                lookup_column_name='platform_igf_id', \
                                                target_column_name='platform_id')       # prepare the function for Platform id
        new_data=data.apply(platform_map_function, axis=1)                              # map platform id foreign key id
        data=new_data                                                                   # overwrite data

      self.store_records(table=Seqrun, data=data)                                       # store without autocommit
      if autosave:
        self.commit_session()
    except:
      if autosave:
        self.rollback_session()
      raise


  def store_seqrun_attributes(self, data, seqrun_id='', autosave=False):
    '''
    A method for storing data to Seqrun_attribute table
    '''
    try:
      if not isinstance(data, pd.DataFrame):
        data=pd.DataFrame(data)                                                             # convert data to dataframe

      if 'seqrun_igf_id' in data.columns:
        seqrun_map_function=lambda x: self.map_foreign_table_and_store_attribute(\
                                               data=x, \
                                               lookup_table=Seqrun, \
                                               lookup_column_name='seqrun_igf_id', \
                                               target_column_name='seqrun_id')              # prepare run mapping function
        new_data=data.apply(seqrun_map_function, axis=1)
        data=new_data                                                                       # overwrite data    

      self.store_attributes(attribute_table=Seqrun_attribute, linked_column='seqrun_id', db_id=seqrun_id, data=data) # store without autocommit
      if autosave:
        self.commit_session()
    except:
      if autosave:
        self.rollback_session()
      raise
      

  def store_seqrun_stats_data(self, data, seqrun_id='', autosave=True):
    '''
    A method for storing data to seqrun_stats table
    '''
    try:
      if not isinstance(data, pd.DataFrame):
        data=pd.DataFrame(data)                                                             # convert data to dataframe

      if 'seqrun_igf_id' in data.columns:
        seqrun_map_function=lambda x: self.map_foreign_table_and_store_attribute(\
                                               data=x, \
                                               lookup_table=Seqrun, \
                                               lookup_column_name='seqrun_igf_id', \
                                               target_column_name='seqrun_id')              # prepare run mapping function
        new_data=data.apply(seqrun_map_function, axis=1)
        data=new_data                                                                       # overwrite data    

      self.store_attributes(attribute_table=Seqrun_stats, linked_column='seqrun_id', db_id=seqrun_id, data=data) # store without autocommit
      if autosave:
        self.commit_session()
    except:
      if autosave:
        self.rollback_session()
      raise
      

  def fetch_seqrun_records_igf_id(self, seqrun_igf_id, target_column_name='seqrun_igf_id'):
    '''
    A method for fetching data for Seqrun table
    required params:
    seqrun_igf_id: an igf id
    target_column_name: a column name in the Seqrun table, default seqrun_igf_id
    '''
    try:
      column=[column for column in Seqrun.__table__.columns \
                       if column.key == target_column_name][0]
      seqrun=self.fetch_records_by_column(table=Seqrun, \
      	                                   column_name=column, \
      	                                   column_id=seqrun_igf_id, \
      	                                   output_mode='one')
      return seqrun  
    except:
      raise


  def fetch_flowcell_barcode_rules_for_seqrun(self,seqrun_igf_id,flowcell_label='flowcell'):
    '''
    A method for fetching flowcell barcode rule for Seqrun
    required param:
    seqrun_igf_id: A seqrun igf id
    '''
    try:
      rules_query = \
        self.session.\
        query(\
          Seqrun.seqrun_igf_id,
          Seqrun_attribute.attribute_value,
          Platform.platform_igf_id,
          Flowcell_barcode_rule.index_1,
          Flowcell_barcode_rule.index_2).\
        join(Seqrun_attribute).\
        join(Platform).\
        join(Flowcell_barcode_rule).\
        filter(Seqrun_attribute.attribute_name==flowcell_label).\
        filter(Seqrun_attribute.attribute_value==Flowcell_barcode_rule.flowcell_type).\
        filter(Seqrun.seqrun_igf_id==seqrun_igf_id)
      rules_data=self.fetch_records(query=rules_query)
      return rules_data
    except:
      raise