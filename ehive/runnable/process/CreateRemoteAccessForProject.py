import os, subprocess
from jinja2 import Template,Environment, FileSystemLoader
from ehive.runnable.IGFBaseProcess import IGFBaseProcess
from igf_data.igfdb.projectadaptor import ProjectAdaptor
from igf_data.utils.fileutils import get_temp_dir
from igf_data.utils.fileutils import copy_remote_file


class CreateRemoteAccessForProject(IGFBaseProcess):
  '''
  Runnable module for creating remote directory for project and copy the htaccess
  file for user access
  '''
  def param_defaults(self):
    params_dict=super(IGFBaseProcess,self).param_defaults()
    params_dict.update({
      'htaccess_template_path':'ht_access',
      'htaccess_template':'htaccess.jinja',
      'htpasswd_template':'htpasswd.jinja',
      'htaccess_filename':'.htaccess',
      'htpasswd_filename':'.htpasswd',
      'remote_project_path':None,
      'remote_user':None,
      'remote_host':None,
    })
    return params_dict
  
  def run(self):
    try:
      seqrun_igf_id=self.param_required('seqrun_igf_id')
      project_name=self.param_required('project_name')
      seqrun_date=self.param_required('seqrun_date')
      flowcell_id=self.param_required('flowcell_id')
      remote_project_path=self.param_required('remote_project_path')
      remote_user=self.param_required('remote_user')
      remote_host=self.param_required('remote_host')
      template_dir=self.param_required('template_dir')
      htaccess_template_path=self.param('htaccess_template_path')
      htaccess_template=self.param('htaccess_template')
      htpasswd_template=self.param('htpasswd_template')
      htaccess_filename=self.param('htaccess_filename')
      htpasswd_filename=self.param('htpasswd_filename')
      
      htaccess_template_path=os.path.join(template_dir,htaccess_template_path)  # set path for template dir
      
      pa=ProjectAdaptor(**{'session_class':igf_session_class})
      pa.start_session()
      user_info=pa.get_project_user_info(project_igf_id=project_name)           # fetch user info from db
      pa.close_session()
      
      user_info=user_info.to_dict(orient='records')                             # convert dataframe to list of dictionaries
      if len(user_info) == 0:
        raise ValueError('No user found for project {0}'.format(project_name)) 
      
      user_list=list()
      user_passwd_dict=dict()
      for user in user_info:
        username=user['username']                                               # get username for irods
        user_list.append(username)
        if 'ht_password' in user.keys():
          ht_passwd=user['ht_password']                                         # get htaccess passwd
          user_passwd_dict.update({username:ht_passwd})
      
      temp_work_dir=get_temp_dir()                                              # get a temp dir
      template_env=Environment(loader=FileSystemLoader(searchpath=htaccess_template_path), \
                               autoescape=select_autoescape(['html', 'xml']))   # set template env
      
      htaccess=template_env.get_template(htaccess_template)                     # read htaccess template
      htpasswd=template_env.get_template(htpasswd_template)                     # read htpass template
      
      htaccess_output=os.path.join(temp_work_dir,htaccess_filename)
      htpasswd_output=os.path.join(temp_work_dir,htpasswd_filename)
      
      htaccess.\
      stream(remote_project_dir=remote_project_path,\
             project_tag=project_name,\
             htpasswd_filename=htpasswd_filename, \
             customerUsernameList=' '.join(user_list)).\
      dump(htaccess_output)                                                     # write new htacces file
      os.chmod(htaccess_output, mode=0o770)
               
      htpasswd.\
      stream(userDict=user_passwd_dict).\
      dump(htpasswd_output)                                                     # write new htpass file
      os.chmod(htpasswd_output, mode=0o770)
      
      remote_project_dir=os.path.join(remote_project_path,\
                                      project_name,\
                                      seqrun_date,
                                      flowcell_id)
      remote_mkdir_cmd=['ssh',\
                       '{0}@{1}'.\
                       format(remote_user,\
                              remote_host),\
                       'mkdir',\
                       '-p',\
                       remote_project_dir]
      subprocess.check_call(remote_mkdir_cmd)
      
      check_htaccess_cmd=['ssh',\
                          '{0}@{1}'.\
                          format(remote_user,\
                                 remote_host),\
                          'ls',\
                          '-a', \
                          os.path.join(remote_project_dir,htaccess_filename)]
      response=subprocess.call(check_htaccess_cmd)
      if response !=0:
        rm_htaccess_cmd=['ssh',\
                         '{0}@{1}'.\
                         format(remote_user,\
                                remote_host),\
                         'rm',\
                         '-f',\
                         os.path.join(remote_project_dir,htaccess_filename)]
        subprocess.check_call(rm_htaccess_cmd)
        
      copy_remote_file(source_path=htaccess_output, \
                       destinationa_path=remote_project_dir, \
                       destination_address=remote_host)                         # copy file to remote
      check_htpasswd_cmd=['ssh',\
                          '{0}@{1}'.\
                          format(remote_user,\
                                 remote_host),\
                          'ls',\
                          '-a', \
                          os.path.join(remote_project_dir,htpasswd_filename)]
      response=subprocess.call(check_htpasswd_cmd)
      if response !=0:
        rm_htpasswd_cmd=['ssh',\
                         '{0}@{1}'.\
                         format(remote_user,\
                                remote_host),\
                         'rm',\
                         '-f',\
                         os.path.join(remote_project_dir,htpasswd_filename)]
        subprocess.check_call(rm_htpasswd_cmd)
        
      copy_remote_file(source_path=htpasswd_output, \
                       destinationa_path=remote_project_dir, \
                       destination_address='{0}@{1}'.format(remote_user,\
                                                            remote_host))       # copy file to remote
      self.param('dataflow_params',{'remote_dir_status':'done'})
    except Exception as e:
      message='seqrun: {2}, Error in {0}: {1}'.format(self.__class__.__name__, \
                                                      e, \
                                                      seqrun_igf_id)
      self.warning(message)
      self.post_message_to_slack(message,reaction='fail')                       # post msg to slack for failed jobs
      raise