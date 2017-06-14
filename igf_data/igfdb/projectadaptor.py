import json
from igf_data.igfdb.baseadaptor import BaseAdaptor
from igf_data.igfdb.igfTables import Project, ProjectUser, Project_attribute

class ProjectAdaptor(BaseAdaptor):
  '''
  An adaptor class for Project, ProjectUser and Project_attribute tables
  '''

  def store_project_data(self, data):
    '''
    Load data to Project table
    '''
    try:
      self.store_records(table=Project, data=data)
    except:
      raise


  def assign_user_to_project(self, data):
    '''
    Load data to ProjectUser table
    required parameters:
    data: a list of dictionaries, each containing 
          'project_igf_id' and 'user_igf_id' as key
          with relevent igf ids as the values.
          an optional key 'data_authority' with 
          boolean value can be provided to set the user 
          as the data authority of the project
          E.g.
          [{'project_igf_id': val, 'user_igf_id': val, 'data_authority':True},] 
    '''
    for project_user in data:
      if not set(('project_igf_id','user_igf_id')).issubset(set(project_user)):                                             # check for required parameters
        raise ValueError('Missing required value in input data {0}'.format(jason.dumps(project_user))) 

      project_user_data=list()                                                                                              # create an empty list
      try:
        project_igf_id=project_user['project_igf_id']
        user_igf_id=project_user['user_igf_id']
        data_authority=''

        if 'data_authority' in project_user and  project_user['data_authority']:
          data_authority='T'

        projects=self.fetch_project_records_igf_id(project_igf_id=project_igf_id, output_mode='object')                      # method from project adaptor
        project_id=projects.next().project_id                                                                                # get project_id from the generator object
        users=self.fetch_records_by_column(table=User, column_name=User.igf_id, column_id=user_igf_id, output_mode='object') # method from base adaptor
        user_id=users.next().user_id                                                                                         # get user_id
        project_user_data.append({'project_id':project_id,'user_id':user_id,'data_authority':data_authority})                # prepare data dictionary and append to list         
      except:
        raise

    try:
      self.store_records(table=ProjectUser, data=data)                                                                       # add to database
    except:
      raise


  def _divide_project_user_dataframe(self, data_frame):
    '''
    An internal method for dividing dataframe for Project and ProjectUser tables
    '''
    pass


  def load_project_and_user_data(self, data):
    '''
    Load data to Project and ProjectUser tables
    required parameter:
    data:  a list of dictionary or a pandas data frame 
    '''
    try:
      (project_data, project_user_data)=self._divide_project_user_dataframe(data=data)
      self.store_project_data(data=project_data)
      self.assign_user_to_project(data=project_user_data)
    except:
      raise


  def store_project_attributes(self, data, project_id):
    '''
    A method for storing data to Project_attribute table
    '''
    try:
      self.store_attributes(attribute_table=Project_attribute, linked_column='project_id', db_id=project_id, data=data)
    except:
      raise


  def fetch_project_records_igf_id(self, project_igf_id, output_mode='dataframe'):
    '''
    A method for fetching data for Project table
    required params:
    project_igf_id: an igf id
     output_mode  : dataframe / object
    '''
    try:
      projects=self.fetch_records_by_column(table=Project, column_name=Project.igf_id, column_id=project_igf_id, output_mode=output_mode )
      return projects  
    except:
      raise
    

  def project_user_info(self, output_mode='dataframe', project_igf_id=''):
    '''
    A method for fetching information from Project, User and ProjectUser table 
    optional params:
    project_igf_id: a project igf id
    output_mode   : dataframe / object
    '''
    if not hasattr(self, 'session'):
      raise AttributeError('Attribute session not found')
  
    session=self.session
    query=session.query(Project).join(ProjectUser).join(User)
    if project_igf_id:
      query=query.filter(Project.igf_id==project_igf_id)
    
    try:    
      results=super(ProjectAdaptor, self).fetch_records(query=query, output_mode=output_mode)
      return results
    except:
      raise
     

  def get_project_attributes(self, project_igf_id, attribute_name=''): 
    projects=self.get_project_info(format='object', project_igf_id=project_igf_id)
    project=projects[0]

    project_attributes=super(ProjectAdaptor, self).get_attributes(attribute_table='Project_attribute', db_id=project.project_id )
    return project_attributes


  def project_samples(self, format='dataframe', project_igf_id=''):
    pass


  def project_experiments(self, format='dataframe', project_igf_id=''):
    pass

  
