"""Independent inherited-domain cases through companion setup/cookie boundary."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime
from itertools import product

import pytest

from acceptance_http import service, BrowserClient, setup_body
from independent_planner_oracle import solve


def configured(service, zone='Etc/UTC'):
    owner = BrowserClient(service)
    body = setup_body(service.secret)
    body['restaurant']['timezone'] = zone
    owner.expect(201, 'POST', '/api/setup', body)
    owner.session()
    return owner, owner.expect(200, 'GET', '/restaurants')['restaurants'][0]['id']


def test_half_open_pairs_failed_keys_and_concurrent_replays(service):
    owner, rid = configured(service)
    body = {'restaurant_id': rid, 'table_ids': ['table_2', 'table_1'], 'starts_at_local': '2032-06-17T18:00', 'party_size': 6}
    owner.expect(422, 'POST', '/reservations', dict(body, table_ids=['table_1', 'table_3']), 'pair', 'combination_not_allowed')
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: owner.request('POST', '/reservations', body, 'pair'), range(8)))
    assert sorted(r.status_code for r in results) == [200] * 7 + [201]
    assert all(r.json() == results[0].json() for r in results)
    original = results[0].json()
    assert original['table_ids'] == ['table_1', 'table_2']
    owner.expect(409, 'POST', '/reservations', dict(body, table_ids=['table_2'], party_size=2, starts_at_local='2032-06-17T18:30'), 'overlap', 'table_unavailable')
    owner.expect(201, 'POST', '/reservations', dict(body, starts_at_local='2032-06-17T19:00'), 'adjacent')


@pytest.mark.parametrize('zone,gap,fold,offset', [('Europe/Berlin','2032-03-28T02:30','2032-10-31T02:30','+02:00'),
                                              ('America/New_York','2032-03-14T02:30','2032-11-07T01:30','-04:00')])
def test_iana_gap_fold_absolute_duration(service, zone, gap, fold, offset):
    owner, rid = configured(service, zone)
    body = {'restaurant_id': rid, 'table_id': 'table_1', 'starts_at_local': gap, 'party_size': 2}
    owner.expect(422, 'POST', '/reservations', body, 'dst', 'invalid_local_time')
    booking = owner.expect(201, 'POST', '/reservations', dict(body, starts_at_local=fold), 'dst')
    assert booking['starts_at'].endswith(offset)
    assert (datetime.fromisoformat(booking['ends_at']) - datetime.fromisoformat(booking['starts_at'])).total_seconds() == 3600


def test_policy_terms_history_series_exception_and_collective_atomicity(service):
    owner, rid = configured(service)
    _, anchor = owner.booking(rid)
    initial_history = owner.expect(200, 'GET', '/reservations/' + anchor['reference'] + '/history')
    terms = deepcopy(anchor['accepted_terms'])
    policy = {k: v for k, v in terms.items() if k != 'policy_version'}
    policy.update(effective_from='2032-01-01', reservation_duration_minutes=90)
    owner.expect(201, 'POST', '/restaurants/' + rid + '/policies', policy, 'policy')
    assert owner.expect(200, 'GET', '/reservations/' + anchor['reference'])['accepted_terms'] == terms
    assert owner.expect(200, 'GET', '/reservations/' + anchor['reference'] + '/history') == initial_history
    agreement = owner.expect(201, 'POST', '/series', {'anchor_reference': anchor['reference'], 'count': 3, 'interval_weeks': 1}, 'adopt')
    sid = agreement['series_id']
    second = agreement['occurrences'][1]['reservation']
    changed = owner.expect(200, 'PATCH', '/reservations/' + second['reference'], {'starts_at_local':'2032-06-24T20:00','expected_revision':second['revision']}, 'exception')
    current = owner.expect(200, 'GET', '/series/' + sid)
    assert current['occurrences'][1]['exception']
    amended = owner.expect(201, 'POST', '/series/' + sid + '/amend', {'from_index':0,'local_time':'21:00','expected_revision':current['revision']}, 'series-amend')
    assert amended['occurrences'][1]['reservation'] == changed
    assert amended['occurrences'][0]['reservation']['starts_at_local'].endswith('21:00')
    assert amended['occurrences'][2]['reservation']['starts_at_local'].endswith('21:00')
    assert amended['occurrences'][0]['reservation']['accepted_terms']['reservation_duration_minutes'] == 90
    before = owner.expect(200, 'GET', '/series/' + sid)
    moves = [{'reference':before['occurrences'][0]['reference'], 'party_size':1},
             {'reference':before['occurrences'][2]['reference'], 'party_size':999}]
    owner.expect(422, 'POST', '/reservation-moves', {'moves':moves}, 'bad-batch', 'party_exceeds_capacity')
    assert owner.expect(200, 'GET', '/series/' + sid) == before


def test_closure_counts_every_overlap_preview_pure_stale_and_replay(service):
    owner, rid = configured(service)
    bookings = []
    for index in range(6):
        _, booking = owner.booking(rid, key=f'b{index}', local=f'2032-06-17T{12+index:02d}:00', table='table_2')
        bookings.append(booking)
    route = '/restaurants/' + rid + '/replans'
    closure = {'table_id':'table_1','from':'2032-06-17T00:00:00+00:00','to':'2032-06-18T00:00:00+00:00'}
    preview = owner.expect(201, 'POST', route, closure, 'preview')
    assert len(preview['assignments']) == 6
    assert preview['moved_count'] == 0
    for booking in bookings:
        assert owner.expect(200, 'GET', '/reservations/' + booking['reference']) == booking
    owner.booking(rid, key='seventh', local='2032-06-17T18:00', table='table_2')
    owner.expect(409, 'POST', route + '/' + preview['plan_id'] + '/apply', {}, 'stale', 'stale_plan')
    owner.expect(422, 'POST', route, closure, 'limit', 'planning_limit')
    # A failed plan key can later be reused for a smaller single global problem.
    small = dict(closure, to='2032-06-17T16:00:00+00:00')
    plan = owner.expect(201, 'POST', route, small, 'limit')
    applied = owner.expect(201, 'POST', route + '/' + plan['plan_id'] + '/apply', {}, 'apply')
    assert owner.expect(200, 'POST', route + '/' + plan['plan_id'] + '/apply', {}, 'apply') == applied
    owner.expect(409, 'POST', '/reservations', {'restaurant_id':rid,'table_id':'table_1','starts_at_local':'2032-06-17T10:00','party_size':2}, 'closed', 'table_unavailable')


@pytest.mark.parametrize('selections,closed', [
    ([(['table_1'],1,'18:00'),(['table_3'],5,'18:00'),(['table_1'],2,'19:00')],'table_1'),
    ([(['table_1'],1,'18:00'),(['table_2'],4,'18:00')],'table_1'),
    ([(['table_1','table_2'],5,'18:00')],'table_2'),
])
def test_planner_matches_independent_exhaustive_oracle(service,selections,closed):
    owner,rid = configured(service)
    bookings=[]
    for index,(tables,party,clock) in enumerate(selections):
        bookings.append(owner.expect(201,'POST','/reservations',{'restaurant_id':rid,'table_ids':tables,
                        'starts_at_local':'2032-06-17T'+clock,'party_size':party},'oracle'+str(index)))
    restaurant=owner.expect(200,'GET','/restaurants/'+rid)
    closure={'table_id':closed,'from':'2032-06-17T17:00:00+00:00','to':'2032-06-17T22:00:00+00:00'}
    expected=solve(restaurant,bookings,closure)
    assert expected is not None
    plan=owner.expect(201,'POST','/restaurants/'+rid+'/replans',closure,'oracle-plan')
    for key in ('assignments','moved_count','unused_seats'):
        assert plan[key] == expected[key]


def test_competing_amendment_cas_and_cutoff_precedence(service):
    owner,rid = configured(service)
    _, booking = owner.booking(rid, table='table_2')
    route='/reservations/'+booking['reference']
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda party:owner.request('PATCH',route,{'party_size':party,'expected_revision':booking['revision']},'cas'+str(party)),(1,3)))
    assert sorted(result.status_code for result in results) == [200,409]
    assert owner.expect(200,'GET',route)['revision'] == booking['revision']+1
    past=owner.expect(201,'POST','/reservations',{'restaurant_id':rid,'table_id':'table_1','starts_at_local':'2020-06-17T18:00','party_size':2},'past')
    route='/reservations/'+past['reference']
    owner.expect(409,'PATCH',route,{'party_size':999,'expected_revision':999},'stale-before-cutoff','stale_revision')
    owner.expect(409,'PATCH',route,{'party_size':999,'expected_revision':past['revision']},'cutoff-before-capacity','cutoff_passed')
    assert owner.expect(200,'GET',route) == past
