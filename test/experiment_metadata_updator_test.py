import unittest,os
from igf_data.utils.dbutils import read_dbconf_json
from sqlalchemy import create_engine
from igf_data.igfdb.igfTables import Base
from igf_data.igfdb.baseadaptor import BaseAdaptor
from igf_data.igfdb.sampleadaptor import SampleAdaptor
from igf_data.igfdb.experimentadaptor import ExperimentAdaptor
from igf_data.process.metadata.experiment_metadata_updator import Experiment_metadata_updator

class Experiment_metadata_updator_test(unittest.TestCase):
  def setUp(self):
    self.dbconfig='data/dbconfig.json'
    dbparam=read_dbconf_json(self.dbconfig)
    base=BaseAdaptor(**dbparam)
    self.engine=base.engine
    self.dbname=dbparam['dbname']
    Base.metadata.create_all(self.engine)
    base.start_session()
    self.session_class=base.get_session_class()
    project_data=[{'project_igf_id':'IGFP0001_test_22-8-2017_rna_sc',
                   'project_name':'test_22-8-2017_rna',
                   'description':'Its project 1',
                   'project_deadline':'Before August 2017',
                   'comments':'Some samples are treated with drug X',
                 }]
    pa=ProjectAdaptor(**{'session':base.session})
    pa.store_project_and_attribute_data(data=project_data)
    sample_data=[{'sample_igf_id':'IGF00001',
                  'project_igf_id':'IGFP0001_test_22-8-2017_rna_sc',
                  'library_source':'TRANSCRIPTOMIC_SINGLE_CELL',
                  'library_strategy':'RNA-SEQ',
                  'experiment_type':'POLYA-RNA'},
                 {'sample_igf_id':'IGF00003',
                  'project_igf_id':'IGFP0001_test_22-8-2017_rna_sc',
                  'library_source':'TRANSCRIPTOMIC_SINGLE_CELL',
                  'experiment_type':'POLYA-RNA'},
                 {'sample_igf_id':'IGF00002',
                  'project_igf_id':'IGFP0001_test_22-8-2017_rna_sc',},
                ]
    sa=SampleAdaptor(**{'session':base.session})
    sa.store_sample_and_attribute_data(data=sample_data)
    experiment_data=[{'project_igf_id':'IGFP0001_test_22-8-2017_rna_sc',
                      'sample_igf_id':'IGF00001',
                      'experiment_igf_id':'IGF00001_HISEQ4000',
                      'library_name':'IGF00001'},
                     {'project_igf_id':'IGFP0001_test_22-8-2017_rna_sc',
                      'sample_igf_id':'IGF00003',
                      'experiment_igf_id':'IGF00003_HISEQ4000',
                      'library_name':'IGF00001'},
                     {'project_igf_id':'IGFP0001_test_22-8-2017_rna_sc',
                      'sample_igf_id':'IGF00002',
                      'experiment_igf_id':'IGF00002_HISEQ4000',
                      'library_name':'IGF00002'},
                    ]
    ea=ExperimentAdaptor(**{'session':base.session})
    ea.store_project_and_attribute_data(data=experiment_data)
    base.close_session()

  def tearDown(self):
    Base.metadata.drop_all(self.engine)
    os.remove(self.dbname)