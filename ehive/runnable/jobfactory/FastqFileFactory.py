import os,fnmatch
from ehive.runnable.IGFBaseJobFactory import IGFBaseJobFactory

class FastqFileFactory(IGFBaseJobFactory):
  '''
  A job factory class for creating fan jobs for demultilexed fastq files
  '''
  def param_defaults(self):
    params_dict=super(IGFBaseJobFactory,self).param_defaults()
    params_dict.update({
        'required_keyword':None,
        'filter_keyword':None,
      })
    return params_dict
  
  
  def run(self):
    try:
      fastq_dir=self.param_required('fastq_dir')
      seqrun_igf_id=self.param_required('seqrun_igf_id')
      required_keyword=self.param_required('required_keyword')
      filter_keyword=self.param_required('filter_keyword')
      
      if not os.path.exists(fastq_dir):
        raise IOError('fastq dir {0} not accessible'.format(fastq_dir))
      fastq_list=list()                                                         # create empty output list
      
      for root, dirs, files in os.walk(top=fastq_dir):
        for file in files:
          if required_keyword and fnmatch.fnmatch(file, required_keyword ):
            fastq_list.append({'fastq_file':os.path.join(root,file)})           # add fastq file to the list if its amatch
            
          elif filter_keyword and not fnmatch.fnmatch(file, filter_keyword ):
            fastq_list.append({'fastq_file':os.path.join(root,file)})           # add fastq file to the list if its not a match
            
      self.param('sub_tasks',fastq_list)                                        # add fastq files to the dataflow
    except Exception as e:
      message='seqrun: {2}, Error in {0}: {1}'.format(self.__class__.__name__, \
                                                      e, \
                                                      seqrun_igf_id)
      self.warning(message)
      self.post_message_to_slack(message,reaction='fail')                       # post msg to slack for failed jobs
      raise