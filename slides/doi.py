'''
Created on 2023-02-12

@author: wf
'''
import urllib.request
import json
import bibtexparser
from dataclasses import dataclass
from pylatexenc.latex2text import LatexNodes2Text

@dataclass
class DOI:
    """
    get DOI data
    """
    doi:str
    debug:bool=False
    
    def debug_dump(self,d:dict):
        """
        dump the given dict if debug mode is on
        
        Args:
            d(dict): the dictionary to dump
        """
        if self.debug:
            print(json.dumps(d,indent=2))
    
    def fetchMeta(self,headers:dict)->dict:
        """
        get the metadata for my doi
        
        Args:
            headers(dict): the headers to use
        
        Returns:
            dict: the metadata according to the given headers
        """
        url=f"https://doi.org/{self.doi}"
        req=urllib.request.Request(url,headers=headers)
        response=urllib.request.urlopen(req)
        encoding = response.headers.get_content_charset('utf-8')
        content = response.read()
        text = content.decode(encoding)
        return text
        
    def fetchBibtexMeta(self)->dict:
        """
        get the meta data for my  doi by getting the bibtext JSON 
        result for the doi
         
        Returns:
            dict: metadata
            
        """
        headers= {
            'Accept': 'application/x-bibtex; charset=utf-8'
        }
        text=self.fetchMeta(headers)
        if self.debug:
            print(text)
        return text
    
    def fetchCiteprocMeta(self)->dict:
        """
        get the meta data for my  doi by getting the Citeproc JSON 
        result for the doi
        
        see https://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html
            
        Returns:
            dict: metadata
        """
        headers= {
            'Accept': 'application/vnd.citationstyles.csl+json; charset=utf-8'
        }
        text=self.fetchMeta(headers)
        json_data=json.loads(text)
        self.debug_dump(json_data)
        return json_data
    
    def fetchBibTexDict(self)->dict:
        """
        get a latex BibTexDict for my doi
            
        Returns:
            dict: a dict with bibliographic metadata in bibtex latex format
        """
        meta_bibtex=self.fetchBibtexMeta()
        bd=bibtexparser.loads(meta_bibtex)
        btex=None
        if len(bd.entries)>0:
            btex=bd.entries[0]
            self.debug_dump(btex)
        return btex
    
    def fetchPlainTextBibTexDict(self)->dict:
        """
        get a plain text BibTexDict for my doi
            
        Returns:
            dict: a dict with bibliographic metadata in bibtex utf-8 (no latex) format
        """
        btex=self.fetchBibTexDict()
        if btex:
            ln2t=LatexNodes2Text()
            for key in btex:
                latex=btex[key]
                no_latex=ln2t.latex_to_text(latex)
                btex[key]=no_latex
            self.debug_dump(btex)
        return btex
        