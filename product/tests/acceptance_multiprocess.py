"""Real two-process Firestore HTTP contention and shared authentication pressure."""
from concurrent.futures import ThreadPoolExecutor
import os
import uuid

import httpx
import pytest

from acceptance_http import Service, BrowserClient, PASSWORD


@pytest.fixture
def pair(tmp_path):
    if not os.environ.get('FIRESTORE_EMULATOR_HOST'):
        pytest.skip('Firestore emulator required')
    config = {'TABLEKEEPER_STORAGE': 'firestore', 'GOOGLE_CLOUD_PROJECT': 'demo-proofline-pilot',
              'TABLEKEEPER_COLLECTION': 'verifier_' + uuid.uuid4().hex}
    for name in ('a', 'b'):
        (tmp_path / name).mkdir()
    a = Service(tmp_path / 'a', overrides=config)
    b = None
    try:
        owner = BrowserClient(a)
        rid = owner.setup()
        config['TABLEKEEPER_PUBLIC_ORIGIN'] = a.url
        b = Service(tmp_path / 'b', overrides=config)
        yield a, b, owner, rid
    finally:
        if b:
            b.close()
        a.close()


def send(url, owner, body, key):
    return httpx.post(url + '/reservations', json=body, cookies=owner.client.cookies,
                      headers={'Origin': owner.service.url, 'X-CSRF-Token': owner.csrf, 'Idempotency-Key': key}, timeout=25)


def test_two_live_processes_same_key_and_competition(pair):
    a, b, owner, rid = pair
    body = {'restaurant_id': rid, 'table_id': 'table_1', 'starts_at_local': '2032-06-17T18:00', 'party_size': 2}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send, server.url, owner, body, 'shared-key') for server in (a, b)]
        responses = [future.result() for future in futures]
    initial = [response.status_code for response in responses]
    for index, response in enumerate(responses):
        if response.status_code == 503:
            # Honest unknown outcome: recover with exact same body and key.
            responses[index] = send((a, b)[index].url, owner, body, 'shared-key')
    recovered = sorted(response.status_code for response in responses)
    print('Same-key HTTP initial/recovered statuses:', initial, recovered)
    assert recovered == [200, 201] or (503 in initial and recovered == [200, 200])
    assert responses[0].json() == responses[1].json()
    original = responses[0].json()
    assert original['revision'] == 1
    for server in (a, b):
        replay = send(server.url, owner, body, 'shared-key')
        assert replay.status_code == 200 and replay.json() == original
    competitor = dict(body, starts_at_local='2032-06-18T18:00')
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send, server.url, owner, competitor, f'competitor-{index}') for index, server in enumerate((a, b))]
        responses = [future.result() for future in futures]
    initial = [response.status_code for response in responses]
    for index, response in enumerate(responses):
        if response.status_code == 503:
            responses[index] = send((a, b)[index].url, owner, competitor, f'competitor-{index}')
    recovered = sorted(response.status_code for response in responses)
    print('Competing-key HTTP initial/recovered statuses:', initial, recovered)
    assert recovered == [201, 409] or (503 in initial and recovered == [200, 409])
    assert len(owner.expect(200, 'GET', '/reservations?limit=50&offset=0')['reservations']) == 2


def test_auth_pressure_shared_between_processes_and_booking_usable(pair):
    a, b, owner, rid = pair
    attacker = BrowserClient(a)
    outcomes = []
    for index in range(10):
        response = httpx.post((a, b)[index % 2].url + '/auth/login',
                              json={'email': 'owner@acceptance.test', 'password': 'wrong-synthetic-password'},
                              cookies=attacker.client.cookies,
                              headers={'Origin': a.url, 'X-CSRF-Token': attacker.csrf,
                                       'X-Forwarded-For': f'192.0.2.{index}', 'X-Forwarded-Proto': 'http'}, timeout=20)
        outcomes.append(response.status_code)
    assert all(status in (401, 429) for status in outcomes)
    assert 429 in outcomes[:9], 'shared per-account throttle must not reset between processes'
    assert outcomes[-1] == 429
    body = {'restaurant_id': rid, 'table_id': 'table_1', 'starts_at_local': '2032-06-17T18:00', 'party_size': 2}
    assert send(b.url, owner, body, 'healthy-booking').status_code == 201
    owner.expect(200, 'POST', '/auth/logout', {})
    assert httpx.get(b.url + '/reservations', cookies=owner.client.cookies, timeout=10).status_code == 401
