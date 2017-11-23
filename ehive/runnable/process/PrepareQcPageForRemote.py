import os, subprocess
from jinja2 import Template,Environment, FileSystemLoader
from ehive.runnable.IGFBaseProcess import IGFBaseProcess
from igf_data.utils.fileutils import get_temp_dir
from igf_data.utils.fileutils import copy_remote_file

class PrepareQcPageForRemote(IGFBaseProcess):
  '''
  Runnable module for creating remote qc page for project and samples.
  Also copy the static html page to remote server
  '''
  def param_defaults(self):
    params_dict=super(IGFBaseProcess,self).param_defaults()
    params_dict.update({
      'qc_template_path':'q_report',
      'project_template':'index.html',
      'sample_template':'sample_level_qc.html',
      'project_filename':'index.html',
      'sample_filename':'sampleQC.html',
      'remote_project_path':None,
      'remote_user':None,
      'remote_host':None,
      'lane_index_info':None
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
      page_type=self.param_required('page_type')
      lane_index_info=self.param_required('lane_index_info') 
      qc_template_path=self.param('qc_template_path')
      project_template=self.param('project_template')
      sample_template=self.param('sample_template')
      project_filename=self.param('project_filename')
      sample_filename=self.param('sample_filename')
     
      
      if page_type not in ['project','sample']:
        raise ValueError('Project type {0} is not defined yet'.format(page_type))
      
      qc_template_path=os.path.join(template_dir,qc_template_path)
      remote_file_path=os.path.join(remote_project_path,\
                                      project_name, \
                                      seqrun_date, \
                                      flowcell_id,\
                                      lane_index_info)                          # generic remote path, lane info is none for project
      
      template_env=Environment(loader=FileSystemLoader(searchpath=qc_template_path), \
                               autoescape=select_autoescape(['xml']))           # set template env
      
      remote_chk_cmd=['ssh',\
                      '{0}@{1}'.\
                      format(remote_user,\
                             remote_host),\
                      'ls']
      
      remote_rm_cmd=['ssh',\
                      '{0}@{1}'.\
                      format(remote_user,\
                             remote_host),\
                      'rm', \
                      '-f']
      
      temp_work_dir=get_temp_dir()                                              # get a temp dir
      
      report_output_file=None
      if page_type == 'project':                                                # prepare project page
        template_file=template_env.get_template(project_template)
        report_output_file=os.path.join(temp_work_dir,project_filename)
        template_file.\
        stream(ProjectName=project_name, \
               SeqrunDate=seqrun_date, \
               FlowcellId=flowcell_id, \
               headerdata=None, \
               qcmain=None, \
              ).\
        dump(report_output_file)
        os.chmod(report_output_file, mode=0o754)
        
        remote_chk_cmd.append(os.path.join(remote_file_path,project_filename))
        remote_rm_cmd.append(os.path.join(remote_file_path,project_filename))
        
      elif page_type == 'sample':                                               # prepare sample page
        if lane_index_info is None:
          raise ValueError('Missing lane and index information')
        
        (lane_id,index_length)=lane_index_info.split('_',1)                     # get lane and index info
        
        template_file=template_env.get_template(sample_template)
        report_output_file=os.path.join(temp_work_dir,sample_filename)
        template_file.\
        stream(ProjectName=project_name, \
               SeqrunDate=seqrun_date, \
               FlowcellId=flowcell_id, \
               Lane=lane_id, \
               IndexBarcodeLength=index_length, \
               headerdata=None, \
               qcmain=None, \
              ).\
        dump(report_output_file)
        os.chmod(report_output_file, mode=0o754)
        
        remote_chk_cmd.append(os.path.join(remote_file_path,sample_filename))
        remote_rm_cmd.append(os.path.join(remote_file_path,sample_filename))
        
      response=subprocess.call(remote_chk_cmd)
      if response!=0:
        subprocess.check_call(remote_rm_cmd)                                    # remove existing remote file
      
      if not os.path.exists(report_output_file):
        raise IOError('file {0} not found'.format(report_output_file))
      
      copy_remote_file(source_path=report_output_file, \
                       destinationa_path=remote_file_path, \
                       destination_address='{0}@{1}'.format(remote_user,\
                                                            remote_host))       # copy file to remote
      self.param('dataflow_params',{'remote_qc_page':\
                                    os.path.join(remote_file_path,
                                                 os.path.basename(report_output_file))})
    except Exception as e:
      message='seqrun: {2}, Error in {0}: {1}'.format(self.__class__.__name__, \
                                                      e, \
                                                      seqrun_igf_id)
      self.warning(message)
      self.post_message_to_slack(message,reaction='fail')                       # post msg to slack for failed jobs
      raise