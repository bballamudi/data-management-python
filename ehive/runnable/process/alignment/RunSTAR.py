import os
from ehive.runnable.IGFBaseProcess import IGFBaseProcess
from igf_data.utils.tools.star_utils import Star_utils
from igf_data.utils.tools.reference_genome_utils import Reference_genome_utils

class RunSTAR(IGFBaseProcess):
  def param_defaults(self):
    params_dict=super(RunSTAR,self).param_defaults()
    params_dict.update({
        'reference_type':'TRANSCRIPTOME_STAR',
        'reference_gtf_type':'GENE_GTF',
        'two_pass_mode':True,
        'run_thread':4,
        'star_patameters':{"--outFilterMultimapNmax":20,
                           "--alignSJoverhangMin":8,
                           "--alignSJDBoverhangMin":1,
                           "--outFilterMismatchNmax":999,
                           "--outFilterMismatchNoverReadLmax":0.04,
                           "--alignIntronMin":20,
                           "--alignIntronMax":1000000,
                           "--alignMatesGapMax":1000000,
                           "--outSAMattributes":"NH HI AS NM MD",
                           "--limitBAMsortRAM":12000000000
                          }
    })
    return params_dict

  def run(self):
    '''
    A method for running STAR alignment
    
    '''
    try:
      project_igf_id=self.param_required('project_igf_id')
      experiment_igf_id=self.param_required('experiment_igf_id')
      sample_igf_id=self.param_required('sample_igf_id')
      run_igf_id=self.param_required('run_igf_id')
      star_exe=self.param_required('star_exe')
      input_fastq_list=self.param_required('input_fastq_list')
      output_prefix=self.param_required('output_prefix')
      run_thread=self.param('run_thread')
      igf_session_class=self.param_required('igf_session_class')
      species_name=self.param('species_name')
      reference_type=self.param('reference_type')
      reference_gtf_type=self.param('reference_gtf_type')
      star_patameters=self.partam('star_patameters')
      two_pass_mode=self.param('two_pass_mode')
      work_dir_prefix=os.path.join(base_work_dir,
                                   project_igf_id,
                                   sample_igf_id,
                                   experiment_igf_id,
                                   run_igf_id)
      work_dir=self.get_job_work_dir(work_dir=work_dir_prefix)                  # get a run work dir
      ref_genome=Reference_genome_utils(\
                   genome_tag=species_name,
                   dbsession_class=igf_session_class,
                   gene_gtf_type=reference_gtf_type,
                   star_ref_type=reference_type)                                # setup ref genome utils
      star_ref=ref_genome.get_transcriptome_star                                # get star ref
      gene_gtf=ref_genome.get_gene_gtf()                                        # get gtf file
      star_obj=Star_utils(star_exe=star_exe,
                          input_files=input_fastq_list,
                          genome_dir=star_ref,
                          reference_gtf=gene_gtf,
                          output_dir=work_dir,
                          output_prefix=output_prefix,
                          threads=run_thread)                                   # set up star for run
      if two_pass_mode is None:
        two_pass_mode=True
      elif two_pass_mode==0:
        two_pass_mode=False                                                     # reset srat twopass mode

      genomic_bam,transcriptomic_bam,star_cmd=\
          star_obj.generate_aligned_bams(two_pass_mode=two_pass_mode,
                                         star_patameters=star_patameters)       # run star cmd
      self.param('dataflow_params',
                   {'star_genomic_bam':genomic_bam,
                    'star_transcriptomic_bam':transcriptomic_bam,
                    'output_prefix':output_prefix
                   })
      message='finished star {0} for {1} {2} {3}'.\
              format(star_cmd,
                     project_igf_id,
                     run_igf_id,
                     output_prefix)
      self.post_message_to_slack(message,reaction='pass')                       # send log to slack
      self.comment_asana_task(task_name=project_igf_id, comment=message)        # send comment to Asana
      message='STAR {0} {1} command: {2}'.\
              format(run_igf_id,
                     output_prefix,
                     star_cmd)
      self.comment_asana_task(task_name=project_igf_id, comment=message)        # send commandline to Asana
    except Exception as e:
      message='project: {2}, sample:{3}, Error in {0}: {1}'.format(self.__class__.__name__, \
                                                      e, \
                                                      project_igf_id,
                                                      sample_igf_id)
      self.warning(message)
      self.post_message_to_slack(message,reaction='fail')                       # post msg to slack for failed jobs
      raise