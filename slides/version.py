'''
Created on 2022-04-01

@author: wf
'''
import slides

class Version(object):
    '''
    Version handling for pysotsog
    '''
    name="pySemanticSlides"
    description='generate Semantic Mediawiki for a set of powerpoint presentations with semantic annotations' 
    version=slides.__version__
    date = '2023-02-14'
    updated = '2023-02-22'
    authors='Wolfgang Fahl'
    doc_url="https://wiki.bitplan.com/index.php/PySemanticSlides"
    chat_url="https://github.com/WolfgangFahl/pySemanticSlides/discussions"
    cm_url="https://github.com/WolfgangFahl/pySemanticSlides"
    license=f'''Copyright 202023 contributors. All rights reserved.
  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0
  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.'''
    longDescription=f"""{name} version {version}
{description}
  Created by {authors} on {date} last updated {updated}"""

        