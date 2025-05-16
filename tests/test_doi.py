"""
Created on 2023-02-12

@author: wf
"""

from slides.doi import DOI
from tests.basetest import Basetest


class TestDOI(Basetest):
    """
    test DOI handling
    """

    def testFetchMeta(self):
        """
        test fetching DOI metadata
        """
        debug = self.debug
        # uncomment to force debug mode
        # debug=True
        doi_str = "10.1145/361598.361623"
        doi = DOI(doi=doi_str, debug=debug)
        meta_json = doi.fetchCiteprocMeta()
        self.assertEqual(doi_str, meta_json["DOI"])
        btex = doi.fetchBibTexDict()
        self.assertEqual("1972", btex["year"])
        self.assertEqual("Communications of the ACM", btex["journal"])
        btex_plain = doi.fetchPlainTextBibTexDict()
        self.assertEqual("Communications of the ACM", btex_plain["journal"])
        pass
