#!/usr/bin/env python
import os
from ehive.runnable.IGFBaseProcess import IGFBaseProcess
from igf_data.task_tracking.igf_slack import IGF_slack
from igf_data.task_tracking.igf_asana import IGF_asana
from igf_data.utils.fileutils import get_temp_dir,remove_dir
from igf_data.process.data_qc.check_sequence_index_barcodes import CheckSequenceIndexBarcodes,IndexBarcodeValidationError
from igf_data.task_tracking import igf_slack

class CheckIndexStats(IGFBaseProcess):
  '''
  A ehive process class for checking barcode stats and report to slack and asana
  '''
  def param_defaults(self):
    params_dict=IGFBaseProcess.param_defaults()
    params_dict.update({
      'stats_filename':'Stats/Stats.json',
      'strict_check':True,
      })
    return params_dict
  
  def run(self):
    try:
      samplesheet_file=self.param_required('original_samplesheet')
      fastq_dir=self.param_required('fastq_dir')
      base_work_dir=self.param_required('base_work_dir')
      stats_filename=self.param('stats_filename')
      seqrun_local_dir=self.param_required('seqrun_local_dir')
      strict_check=self.param('strict_check')
      igf_slack=self.param('igf_slack')
      igf_asana=self.param('igf_asana')
      job_name=self.job_name()
      work_dir=get_temp_dir                                                     # get work directory name
      seqrun_name=os.path.basename(seqrun_local_dir)                            # get seqrun name
      stats_json_file=os.path.join(fastq_dir,stats_filename)                    # get stats file path
      barcode_stat=CheckSequenceIndexBarcodes(stats_json_file,samplesheet_file) # create check instance
      barcode_stat.validate_barcode_stats(work_dir=work_dir, \
                                          strict_check=strict_check)            # validate seqrun stats
      self.param('dataflow_params',{'barcode_qc_stats':'PASS'})                 # seed dataflow only of the qc passed lanes
    except IndexBarcodeValidationError as e:
      for plot_file in e.plots:
        self.post_file_to_slack(message=e.message,file=plot_file)               # posting plot files to slack
        self.upload_file_to_asana_task(task_name=seqrun_name, \
                                       filepath=plot_file, \
                                       comment=e.message)                       # upload plots to asana
    except Exception:
          raise