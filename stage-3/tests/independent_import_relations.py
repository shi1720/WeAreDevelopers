"""Source-review regressions for portable stage-3 state relationships."""
import copy
import unittest
from independent_series import IndependentSeries


class IndependentImportRelations(IndependentSeries):
    def test_import_cannot_erase_permanent_series_exception(self):
        anchor=self.create(); series=self.adopt(anchor)
        reference=series['occurrences'][1]['reference']
        self.expect(200,'PATCH','/reservations/'+reference,{'party_size':1},self.a)
        before=self.snapshot(); corrupt=copy.deepcopy(before)
        corrupt['state']['series'][series['series_id']]['occurrences'][1]['exception']=False
        self.expect(422,'POST','/_test/import',corrupt,code='validation_failed')
        self.assertTrue(before==self.snapshot())


def load_tests(loader,tests,pattern):
    return unittest.TestSuite(IndependentImportRelations(name) for name in IndependentImportRelations.__dict__ if name.startswith('test_'))
