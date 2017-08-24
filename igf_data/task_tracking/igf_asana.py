import asana, json

class IGF_asana:
  '''
  A python class for accessing Asana
  required params:
  asana_config: A json config file with personal token
                e.g. { "asana_personal_token" : "zyx" }
  asana_project_id: A project id
  '''

  def __init__(self, asana_config, asana_project_id, **asana_label):
    asana_label.setdefault('asana_personal_token_label','asana_personal_token')       
    self.asana_personal_token_label=asana_label['asana_personal_token_label']
        
    self.asana_personal_token=None       
    self.asana_config=asana_config 
    self.asana_project_id=asana_project_id                                 # project name can change, project id is stable     
    self._read_and_set_asana_config()                                      # read config file and set parameters
    self.asanaclient=asana.Client.access_token(self.asana_personal_token)  # create asana client instance
    self.asana_personal_token=None                                         # reset asana token value
    self._get_user_details()                                               # load user information
    self._check_project_id()                                               # check user given project id
  

  def get_asana_task_id(self, task_name):
    '''
    A method for fetching task id from asana server
    required param:
    task_name: A task name
    '''
    asana_task_id=None
    matched_tasks=list()
    try:
      matched_tasks=[p for p in self.asanaclient.tasks.find_all({'project':self.asana_project_id}) if p['name']==task_name]
      asana_task_id=matched_tasks[0]['id']
    except:
      pass
        
    if len(matched_tasks) > 1:
      raise ValuesError('received more than one entry for task: {0}'.format(task_name))

    return asana_task_id
        
        
  def create_asana_task(self,task_name, notes=''):
    '''
    A method for creating new task in Asana. Tasks will get assigned to the creator.
    required params:
    task_name: A task name
    optional:
    notes: A task description
    '''
    task_id=None
    try:
      results=self.asanaclient.tasks.create_in_workspace( \
                                            self.asana_workspace_id,\
                                            {'name':task_name, \
                                             'projects':self.asana_project_id, \
                                             'notes':notes,
                                             'assignee':self.asana_user_id,
                                            })
      task_id=results['id']
      return task_id
    except:
      raise                          
    
    
  def fetch_task_id_for_task_name(self, task_name):
    '''
    A method for fetching task id from asana. It will create a ne task
    if its not present yet
    required params:
    task_name: A task name
    
    return: asana task id
    '''
    task_id=self.get_asana_task_id(task_name)
    if task_id is None:
      task_id=self.create_asana_task(task_name)

    return task_id   
    
    
  def comment_asana_task(self, task_name, comment):
    '''
    A method for adding comments to asana tasks. Task will be created if it doesn't exist.
    required params:
    task_name: A task name
    comment: A comment for the target task
  
    returns:
     A output story as dictionary
    '''
    try:
      asana_task_id=self.fetch_task_id_for_task_name(task_name)
      res=self.asanaclient.stories.create_on_task(asana_task_id,{'text':comment})
      return res
    except:
      raise
    
    
  def _check_project_id(self):
    '''
    An internal method for checking user given project id
    '''
    matched_projects=[p for p in self.asanaclient.projects.\
                                   find_all({'workspace':self.asana_workspace_id}) \
                                     if p['id']==int(self.asana_project_id) ]
    if len(matched_projects)==0:
      raise ValueError('project id {0} not found in workspace {1}'.format(self.asana_project_id,self.asana_workspace_name))
        
        
  def _get_user_details(self):
    '''
    An internal method for loading user and workspace information
    '''
    try:
      user_detail=self.asanaclient.users.me()
      self.asana_workspace_id=user_detail['workspaces'][0]['id']
      self.asana_workspace_name=user_detail['workspaces'][0]['name']
      self.asana_user_id=user_detail['id']
      self.asana_user_name=user_detail['name']
    except:
      raise
        
        
  def  _read_and_set_asana_config(self):
    '''
    An internal method for reading asana config json file
    '''
    asana_params=dict()
    with open(self.asana_config,'r') as json_data:
      asana_params=json.load(json_data)
    if self.asana_personal_token_label in asana_params:
      self.asana_personal_token=asana_params[self.asana_personal_token_label]
        