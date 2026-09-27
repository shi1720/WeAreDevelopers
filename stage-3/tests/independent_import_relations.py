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

    def test_valid_pre_adoption_change_reversion_cancel_and_corrupt_relations(self):
        anchor=self.create(); path='/reservations/'+anchor['reference']
        self.expect(200,'PATCH',path,{'party_size':1},self.a)
        series=self.adopt(anchor)
        self.assertFalse(series['occurrences'][0]['exception'])
        second=series['occurrences'][1]['reference']
        self.expect(200,'PATCH','/reservations/'+second,{'party_size':2},self.a)
        self.expect(200,'PATCH','/reservations/'+second,{'party_size':1},self.a)
        self.expect(200,'POST','/reservations/'+second+'/cancel',{},self.a)
        before=self.snapshot()
        self.expect(204,'POST','/_test/import',before)
        self.assertTrue(before==self.snapshot())
        mutations=[
            lambda s:s['series'][series['series_id']]['occurrences'][0].update(exception=True),
            lambda s:s['series'][series['series_id']]['occurrences'][1].update(exception=False),
            lambda s:s['series'][series['series_id']]['occurrences'][1].update(index=0),
            lambda s:s['series'][series['series_id']]['occurrences'][1].update(reference=anchor['reference']),
            lambda s:s['histories'][second][1].update(seq=99),
            lambda s:s['histories'][second][0]['accepted_terms'].update(reservation_duration_minutes=999),
            lambda s:s.update(receipts=[r for r in s['receipts'] if r['path']!='/series']),
        ]
        for mutation in mutations:
            corrupt=copy.deepcopy(before);mutation(corrupt['state'])
            self.expect(422,'POST','/_test/import',corrupt,code='validation_failed')
            self.assertTrue(before==self.snapshot())


def load_tests(loader,tests,pattern):
    return unittest.TestSuite(IndependentImportRelations(name) for name in IndependentImportRelations.__dict__ if name.startswith('test_'))
