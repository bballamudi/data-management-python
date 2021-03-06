from bs4 import BeautifulSoup

class RunParameter_xml:
  '''
  A class for reading runparameters xml file from Illumina sequencing runs
  
  :param xml_file: A runparameters xml file
  '''
  def __init__(self, xml_file):
    self.xml_file=xml_file
    self._read_xml()


  def _read_xml(self):
    '''
    Internal function for reading the xml file using BS4
    '''
    xml_file=self.xml_file
    with open(xml_file, 'r') as fp:
      soup = BeautifulSoup(fp, "html5lib")
    self._soup = soup


  def get_hiseq_flowcell(self):
    '''
    A method for fetching flowcell details for hiseq run
    
    :returns: Flowcell info or None (for MiSeq and NextSeq runs)
    '''
    soup=self._soup
    try:
      if soup.flowcell:
        flowcell=soup.flowcell.contents[0]
      else:
        flowcell=None
      return flowcell
    except:
      raise



