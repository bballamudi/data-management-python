import unittest, os
import pandas as pd
from igf_data.illumina.samplesheet import SampleSheet
from igf_data.process.singlecell_seqrun.processsinglecellsamplesheet import ProcessSingleCellSamplesheet

class ProcessSingleCellSamplesheet_testA(unittest.TestCase):
  def setUp(self):
    self.samplesheet_file='data/singlecell_data/SampleSheet.csv'
    self.singlecell_barcode_json='data/singlecell_data/chromium-shared-sample-indexes-plate_20180301.json'
    self.output_file='data/singlecell_data/mod_SampleSheet.csv'
    if os.path.exists(self.output_file):
      os.remove(self.output_file)

  def tearDown(self):
    if os.path.exists(self.output_file):
      os.remove(self.output_file)

  def test_change_singlecell_barcodes1(self):
    sc_data=ProcessSingleCellSamplesheet(samplesheet_file=self.samplesheet_file,\
                                         singlecell_barcode_json=self.singlecell_barcode_json)
    sc_data.change_singlecell_barcodes(output_samplesheet=self.output_file)
    sc_samplesheet=SampleSheet(infile=self.output_file)
    sc_samplesheet.filter_sample_data(condition_key='Sample_Project',\
                                      condition_value='project_2', \
                                      method='include')
    self.assertEqual(len(sc_samplesheet._data),8)
    sc_samplesheet.filter_sample_data(condition_key='Sample_ID',\
                                      condition_value='IGF0008_1', \
                                      method='include')
    self.assertEqual(len(sc_samplesheet._data),1)
    sc_index=sc_samplesheet._data[0]['index']
    self.assertTrue(sc_index , ["GTGTATTA", "TGTGCGGG", "ACCATAAC", "CAACGCCT"])
    self.assertEqual(sc_samplesheet._data[0]['Original_index'],'SI-GA-B3')
    self.assertEqual(sc_samplesheet._data[0]['Original_Sample_ID'],'IGF0008')

  def test_change_singlecell_barcodes2(self):
    sc_data=ProcessSingleCellSamplesheet(samplesheet_file=self.samplesheet_file,\
                                         singlecell_barcode_json=self.singlecell_barcode_json)
    sc_data.change_singlecell_barcodes(output_samplesheet=self.output_file)
    samplesheet=SampleSheet(infile=self.output_file)
    samplesheet.filter_sample_data(condition_key='Sample_Project',\
                                   condition_value='project_2', \
                                   method='exclude')
    self.assertEqual(len(samplesheet._data),5)
    self.assertTrue('Original_Sample_ID' in samplesheet._data_header)

class ProcessSingleCellSamplesheet_testB(unittest.TestCase):
  def setUp(self):
    self.samplesheet_file='data/singlecell_data/SampleSheet_10x_NA.csv'
    self.singlecell_barcode_json='data/singlecell_data/chromium-shared-sample-indexes-plate_20180301.json'
    self.output_file='data/singlecell_data/mod_SampleSheet.csv'
    if os.path.exists(self.output_file):
      os.remove(self.output_file)

  def tearDown(self):
    if os.path.exists(self.output_file):
      os.remove(self.output_file)

  def test_change_singlecell_barcodes3(self):
    sc_data = \
      ProcessSingleCellSamplesheet(\
        samplesheet_file=self.samplesheet_file,
        singlecell_barcode_json=self.singlecell_barcode_json)
    sc_data.\
      change_singlecell_barcodes(output_samplesheet=self.output_file)
    sc_samplesheet = \
      SampleSheet(infile=self.output_file)
    sc_samplesheet.\
      filter_sample_data(\
        condition_key='Sample_Project',
        condition_value='project_3',
        method='include')
    sc_index = sc_samplesheet._data[0]['index']
    self.assertTrue(sc_index in ("AAACGGCG","CCTACCAT","GGCGTTTC","TTGTAAGA"))

if __name__=='__main__':
  unittest.main()
