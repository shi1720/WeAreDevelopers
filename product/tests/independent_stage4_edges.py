"""Additional frozen-candidate checks; no service implementation imports."""
import copy
import unittest
from datetime import datetime, timedelta, timezone
from independent_replans import IndependentReplans
from independent_series_amend import IndependentSeriesAmend
from independent_policies import policy_fixture


class IndependentStage4Edges(IndependentReplans, IndependentSeriesAmend):
    def test_other_restaurant_changes_do_not_stale_plan(self):
        data = policy_fixture()
        other = copy.deepcopy(data['restaurants'][0]); other['id'] = 'other'
        data['restaurants'].append(other)
        self.reset(data); self.a, self.b = self.login(), self.login('bea@example.test')
        self.create(); plan = self.preview()
        self.expect(201, 'POST', '/restaurants/other/replans', self.closure(), self.b, 'other-preview')
        other_plan = self.expect(201, 'POST', '/restaurants/other/replans', self.closure(), self.b, 'other-preview-2')
        self.expect(201, 'POST', '/restaurants/other/replans/'+other_plan['plan_id']+'/apply', {}, self.b, 'other-apply')
        self.expect(404, 'POST', '/restaurants/other/replans/'+plan['plan_id']+'/apply', {}, self.b, 'wrong', 'not_found')
        result = self.apply(plan)
        self.create(key='later', table='table-m', local='2032-06-17T21:00')
        self.assertEqual(result, self.expect(200, 'POST', self.path+'/'+plan['plan_id']+'/apply', {}, self.b, 'apply'))

    def test_plan_series_revision_once_and_atomic_snapshot_reads(self):
        series = self.adopt(self.create())
        closure = self.closure(); closure['to'] = '2032-07-02T00:00:00+00:00'
        plan = self.preview(closure)
        before = self.snapshot()['state']
        def race(i):
            return self.request('POST', self.path+'/'+plan['plan_id']+'/apply', {}, self.b, 'race') if i % 2 else self.request('GET', '/_test/export')
        results = self.concurrent(50, race)
        after = self.snapshot()['state']
        self.assertEqual(sum(status == 201 for status, _ in results), 1)
        for i, (status, body) in enumerate(results):
            if i % 2:
                self.assertIn(status, (200, 201))
            else:
                self.assertEqual(status, 200)
                observed = body['state']
                # Compare one complete snapshot, never independently sampled records.
                self.assertTrue(any(all(observed[k] == state[k] for k in ('reservations', 'histories', 'series', 'closures', 'restaurant_revisions')) for state in (before, after)))
        current = self.current(series)
        self.assertEqual(current['revision'], 2)
        self.assertEqual([o['exception'] for o in current['occurrences']], [False]*3)
        for old, new in zip(series['occurrences'], current['occurrences']):
            self.assertEqual(old['reference'], new['reference'])
            self.assertEqual(old['reservation']['accepted_terms'], new['reservation']['accepted_terms'])
        self.assertEqual(before['series'][series['series_id']]['occurrences'], after['series'][series['series_id']]['occurrences'])

    def test_amend_dst_gap_and_nonoccupancy_precedence(self):
        data = policy_fixture(); data['restaurants'][0]['timezone'] = 'America/New_York'
        self.reset(data); self.a, self.b = self.login(), self.login('bea@example.test')
        series = self.adopt(self.create(local='2032-03-07T18:00'), count=2)
        self.create(key='block', local='2032-03-07T02:30')
        before = self.snapshot()
        self.expect(422, 'POST', self.amend_path(series), {'expected_revision':1,'from_index':0,'local_time':'02:30'}, self.a, 'gap', 'invalid_local_time')
        self.assertTrue(before == self.snapshot())

    def test_amend_old_cutoff_and_stale_precedence(self):
        data = policy_fixture()
        self.reset(data); self.a, self.b = self.login(), self.login('bea@example.test')
        day = (datetime.now(timezone.utc)+timedelta(days=1)).date().isoformat()
        series = self.adopt(self.create(local=day+'T18:00'))
        self.publish(date=day, cancellation_cutoff_minutes=10080)
        self.expect(201, 'POST', self.amend_path(series), {'expected_revision':1,'from_index':0,'local_time':'19:00'}, self.a, 'adopt-cutoff')
        self.publish(date=day, cancellation_cutoff_minutes=0, key='replace-cutoff')
        before = self.snapshot()
        body = {'expected_revision':1,'from_index':0,'local_time':'20:00'}
        self.expect(409, 'POST', self.amend_path(series), body, self.a, 'retry', 'stale_revision')
        body['expected_revision'] = 2
        self.expect(409, 'POST', self.amend_path(series), body, self.a, 'retry', 'cutoff_passed')
        self.assertTrue(before == self.snapshot())

    def test_unapplied_applied_and_history_corruption_is_atomic(self):
        self.create(); plan = self.preview(); pid = plan['plan_id']
        for applied in (False, True):
            if applied: self.apply(plan)
            baseline = self.snapshot()
            self.expect(204, 'POST', '/_test/import', baseline)
            mutations = [
                lambda s: s['plans'][pid]['preview'].update(moved_count=99),
                lambda s: s['plans'][pid]['preview']['assignments'][0].update(table_ids=['missing']),
                lambda s: s['plans'][pid].update(applied=not applied),
                lambda s: s['plans'][pid].update(before=[]),
                lambda s: s.update(receipts=[r for r in s['receipts'] if r['path'] != self.path]),
            ]
            if applied:
                ref = plan['assignments'][0]['reference']
                mutations += [lambda s: s.update(closures=[]), lambda s: s['histories'][ref][-1].update(plan_id='missing')]
            for mutate in mutations:
                corrupt = copy.deepcopy(baseline); mutate(corrupt['state'])
                self.expect(422, 'POST', '/_test/import', corrupt, code='validation_failed')
                self.assertTrue(baseline == self.snapshot())

    def test_amend_closure_rollback_policy_noop_and_provenance(self):
        series = self.adopt(self.create())
        self.publish(date='2032-06-24', reservation_duration_minutes=120)
        body = {'expected_revision':1,'from_index':0,'local_time':'18:00'}
        unchanged = self.expect(201, 'POST', self.amend_path(series), body, self.a, 'noop-policy')
        self.assertEqual(unchanged, series)
        body['local_time'] = '20:00'
        changed = self.expect(201, 'POST', self.amend_path(series), body, self.a, 'policy-amend')
        self.assertEqual([o['reservation']['accepted_terms']['policy_version'] for o in changed['occurrences']], [0,1,1])
        closure = {'table_id':'table-z','from':'2032-07-01T22:00:00+00:00','to':'2032-07-01T23:00:00+00:00'}
        self.apply(self.preview(closure))
        before = self.snapshot()
        self.expect(409, 'POST', self.amend_path(series), {'expected_revision':2,'from_index':0,'local_time':'21:30'}, self.a, 'blocked', 'table_unavailable')
        self.assertTrue(before == self.snapshot())
        self.expect(204, 'POST', '/_test/import', before)
        self.assertEqual(changed, self.expect(200, 'POST', self.amend_path(series), body, self.a, 'policy-amend'))
        for mutate in (
            lambda s:s.update(series_operations=[]),
            lambda s:s['series_operations'][-1]['body'].update(local_time='21:00'),
            lambda s:s['series_operations'][-1]['after'].update(revision=99),
            lambda s:s.update(receipts=[r for r in s['receipts'] if r['path'] != self.amend_path(series)]),
        ):
            corrupt = copy.deepcopy(before); mutate(corrupt['state'])
            self.expect(422, 'POST', '/_test/import', corrupt, code='validation_failed')
            self.assertTrue(before == self.snapshot())


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(IndependentStage4Edges(name) for name in IndependentStage4Edges.__dict__ if name.startswith('test_'))
