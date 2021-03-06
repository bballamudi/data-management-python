import unittest, json, os, shutil
from sqlalchemy import create_engine
from igf_data.igfdb.igfTables import Base, Seqrun, Pipeline_seed, Pipeline, ProjectUser
from igf_data.igfdb.baseadaptor import BaseAdaptor
from igf_data.igfdb.platformadaptor import PlatformAdaptor
from igf_data.igfdb.projectadaptor import ProjectAdaptor
from igf_data.igfdb.useradaptor import UserAdaptor
from igf_data.igfdb.sampleadaptor import SampleAdaptor
from igf_data.igfdb.seqrunadaptor import SeqrunAdaptor
from igf_data.igfdb.pipelineadaptor import PipelineAdaptor
from igf_data.process.seqrun_processing.find_and_process_new_seqrun import find_new_seqrun_dir,calculate_file_md5,load_seqrun_files_to_db, seed_pipeline_table_for_new_seqrun, check_for_registered_project_and_sample,validate_samplesheet_for_seqrun

class Find_seqrun_test1(unittest.TestCase):
  def setUp(self):
    self.path = 'data/seqrun_dir'
    self.dbconfig = 'data/dbconfig.json'
    self.md5_out_path = 'data/md5_dir'
    self.pipeline_name = 'demultiplexing_fastq'

    seqrun_json='data/seqrun_db_data.json'
    platform_json='data/platform_db_data.json'
    pipeline_json='data/pipeline_data.json'

    os.mkdir(self.md5_out_path)
    dbparam = None
    with open(self.dbconfig, 'r') as json_data:
      dbparam = json.load(json_data)
    base = BaseAdaptor(**dbparam)
    self.engine = base.engine
    self.dbname=dbparam['dbname']
    self.pipeline_name=''
    Base.metadata.create_all(self.engine)
    base.start_session()
    user_data=[{'name':'user1','email_id':'user1@ic.ac.uk','username':'user1'},]
    ua=UserAdaptor(**{'session':base.session})
    ua.store_user_data(data=user_data)
    project_data=[{'project_igf_id':'project_1',
                   'project_name':'test_22-8-2017_rna',
                   'description':'Its project 1',
                   'project_deadline':'Before August 2017',
                   'comments':'Some samples are treated with drug X',
                 }]
    pa=ProjectAdaptor(**{'session':base.session})
    pa.store_project_and_attribute_data(data=project_data)
    project_user_data=[{'project_igf_id':'project_1',
                        'email_id':'user1@ic.ac.uk',
                        'data_authority': True}]
    pa.assign_user_to_project(data=project_user_data)
    sample_data=[{'sample_igf_id':'IGF0001',
                  'project_igf_id':'project_1',},
                 {'sample_igf_id':'IGF0002',
                  'project_igf_id':'project_1',},
                 {'sample_igf_id':'IGF0003',
                  'project_igf_id':'project_1',},
                ]
    sa=SampleAdaptor(**{'session':base.session})
    sa.store_sample_and_attribute_data(data=sample_data)
    base.commit_session()
    with open(pipeline_json, 'r') as json_data:            # store pipeline data to db
      pipeline_data=json.load(json_data)
      pa=PipelineAdaptor(**{'session':base.session})
      pa.store_pipeline_data(data=pipeline_data)
      
    with open(platform_json, 'r') as json_data:            # store platform data to db
      platform_data=json.load(json_data)
      pl=PlatformAdaptor(**{'session':base.session})
      pl.store_platform_data(data=platform_data)
        
    with open(seqrun_json, 'r') as json_data:              # store seqrun data to db
      seqrun_data=json.load(json_data)
      sra=SeqrunAdaptor(**{'session':base.session})
      sra.store_seqrun_and_attribute_data(data=seqrun_data)
      base.close_session()

  def tearDown(self):
     #shutil.copyfile(self.dbname, 'test.db')
     Base.metadata.drop_all(self.engine)
     os.remove(self.dbname)
     shutil.rmtree(self.md5_out_path, ignore_errors=False, onerror=None)

  def test_find_new_seqrun_dir(self):
    valid_seqrun_dir=find_new_seqrun_dir(path=self.path,dbconfig=self.dbconfig) 
    self.assertEqual(list(valid_seqrun_dir.keys())[0],'seqrun1')

  def test_calculate_file_md5(self):
    valid_seqrun_dir=find_new_seqrun_dir(path=self.path,dbconfig=self.dbconfig) 
    new_seqrun_and_md5=calculate_file_md5(seqrun_info=valid_seqrun_dir, md5_out=self.md5_out_path, seqrun_path=self.path)
    md5_file_name=new_seqrun_and_md5['seqrun1']
    with open(md5_file_name, 'r') as json_data:
      md5_data=json.load(json_data)
    shutil.rmtree(self.md5_out_path, ignore_errors=False, onerror=None)
    os.mkdir(self.md5_out_path)
    md5_value=[row['file_md5'] for row in md5_data for file_key,file_val in row.items() if file_key=='seqrun_file_name' and file_val=='RTAComplete.txt'][0]
    self.assertEqual(md5_value, "c514939fdd61df26b103925a5122b356")

  def test_load_seqrun_files_to_db(self):
    valid_seqrun_dir=find_new_seqrun_dir(path=self.path,dbconfig=self.dbconfig)
    new_seqrun_and_md5=calculate_file_md5(seqrun_info=valid_seqrun_dir, md5_out=self.md5_out_path, seqrun_path=self.path) 
    load_seqrun_files_to_db(seqrun_info=valid_seqrun_dir, seqrun_md5_info=new_seqrun_and_md5, dbconfig=self.dbconfig)

    # check in db
    dbparam = None
    with open(self.dbconfig, 'r') as json_data:
      dbparam = json.load(json_data)
    sra=SeqrunAdaptor(**dbparam)
    sra.start_session()
    sra_data=sra.fetch_seqrun_records_igf_id(seqrun_igf_id='seqrun1')
    sra.close_session()
    self.assertEqual(sra_data.flowcell_id, 'HXXXXXXXX')

    seed_pipeline_table_for_new_seqrun(pipeline_name='demultiplexing_fastq', dbconfig=self.dbconfig)
    # check in db
    dbparam = None
    with open(self.dbconfig, 'r') as json_data:
      dbparam = json.load(json_data)   

    base=BaseAdaptor(**dbparam)
    base.start_session()
    seeds=base.fetch_records(query=base.session.query(Seqrun.seqrun_igf_id).\
                                   join(Pipeline_seed, Pipeline_seed.seed_id==Seqrun.seqrun_id).\
                                   join(Pipeline, Pipeline.pipeline_id==Pipeline_seed.pipeline_id).\
                                   filter(Pipeline.pipeline_name=='demultiplexing_fastq').\
                                   filter(Pipeline_seed.seed_table=='seqrun'), output_mode='object')
    base.close_session()
    self.assertTrue('seqrun1' in [s.seqrun_igf_id for s in seeds])
 
  def test_check_for_registered_project_and_sample(self):
    valid_seqrun_dir=find_new_seqrun_dir(path=self.path,dbconfig=self.dbconfig)
    registered_seqruns,msg=check_for_registered_project_and_sample(seqrun_info=valid_seqrun_dir,\
                                                                   dbconfig=self.dbconfig)
    self.assertEqual(msg,'')
    self.assertTrue('seqrun1' in registered_seqruns)
if __name__=='__main__':
  unittest.main()

