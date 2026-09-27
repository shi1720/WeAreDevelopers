"""Cross-record checks for portable plans and collective amendment provenance."""
from copy import deepcopy
from urllib.parse import unquote
import re
from . import planner


def checked_public(state, value, user):
    from .state import require, validate_record, validate_historical_response
    require(type(value) is dict and 'user_id' not in value)
    record = dict(value, user_id=user)
    validate_record(record, state)
    ref = record['reference']
    require(ref in state['reservations'])
    current = state['reservations'][ref]
    require(all(record[k] == current[k] for k in ('reservation_id', 'restaurant_id', 'user_id', 'created_at')))
    validate_historical_response(state, record)
    return record


def validate_operations(state):
    from .state import require, integer
    from .validation import canonical
    collective = set()
    for operation in state['series_operations']:
        require(type(operation) is dict)
        sid = operation.get('series_id')
        require(type(sid) is str and sid in state['series'])
        agreement = state['series'][sid]
        before, after, body = (operation.get(k) for k in ('before', 'after', 'body'))
        require(type(before) is dict and type(after) is dict and type(body) is dict)
        first, clock = body.get('from_index'), body.get('local_time')
        require(type(first) is int and 0 <= first < len(agreement['occurrences']))
        require(type(clock) is str and re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', clock) is not None)
        require(integer(body.get('expected_revision'), 1) and body['expected_revision'] == before.get('revision'))
        require(integer(after.get('revision'), 1) and after['revision'] <= agreement['revision'])
        for snapshot in (before, after):
            require(snapshot.get('series_id') == sid and snapshot.get('interval_weeks') == agreement['interval_weeks'])
            require(type(snapshot.get('occurrences')) is list and len(snapshot['occurrences']) == len(agreement['occurrences']))
        changed = False
        for index, (old, new, member) in enumerate(zip(before['occurrences'], after['occurrences'], agreement['occurrences'])):
            require(type(old) is dict and type(new) is dict)
            require(old.get('index') == new.get('index') == index and type(old['index']) is int and type(new['index']) is int)
            require(old.get('reference') == new.get('reference') == member['reference'])
            require(type(old.get('exception')) is bool and new.get('exception') is old['exception'])
            a = checked_public(state, old.get('reservation'), agreement['user_id'])
            b = checked_public(state, new.get('reservation'), agreement['user_id'])
            require(a['reference'] == b['reference'] == member['reference'])
            local = member['scheduled_date'] + 'T' + clock
            eligible = index >= first and not old['exception'] and a['status'] == 'confirmed'
            if not eligible or a['starts_at_local'] == local:
                require(canonical(a) == canonical(b))
                continue
            changed = True
            require(b['revision'] == a['revision'] + 1 and b['starts_at_local'] == local)
            require(all(a[k] == b[k] for k in ('reference', 'table_ids', 'party_size', 'status')))
            entry = state['histories'][b['reference']][b['revision'] - 1]
            require(entry['event'] == 'changed' and entry['changes'] == [{'field': 'starts_at_local', 'from': a['starts_at_local'], 'to': local}])
            pair = (b['reference'], b['revision'])
            require(pair not in collective)
            collective.add(pair)
        require(after['revision'] == before['revision'] + int(changed))
        require(any(type(r) is dict and r.get('path') == '/series/' + sid + '/amend'
                    and r.get('user_id') == agreement['user_id'] and canonical(r.get('body')) == canonical(body)
                    and canonical(r.get('response')) == canonical(after) for r in state['receipts']))
    return collective


def validate_plans(state):
    from .state import require, ident, integer, validate_record, validate_historical_response
    from .replans import closure
    from .reservations import restaurant_for
    from .validation import canonical
    require(type(state['closures']) is list)
    applied = set()
    for c in state['closures']:
        require(type(c) is dict and ident(c.get('plan_id')) and c['plan_id'] in state['plans'])
        plan = state['plans'][c['plan_id']]
        require(c == dict(plan['preview']['closure'], restaurant_id=plan['restaurant_id'], plan_id=c['plan_id']))
        require(c['plan_id'] not in applied and plan['applied'] is True)
        applied.add(c['plan_id'])
    for pid, plan in state['plans'].items():
        require(ident(pid) and type(plan) is dict and type(plan.get('applied')) is bool)
        restaurant = restaurant_for(state, plan.get('restaurant_id'))
        preview = plan.get('preview')
        require(type(preview) is dict and preview.get('plan_id') == pid)
        require(integer(preview.get('restaurant_revision')) and preview['restaurant_revision'] <= state['restaurant_revisions'][restaurant['id']])
        proposed = closure(restaurant, preview.get('closure', {}))
        require(type(plan.get('context')) is list and type(plan.get('before')) is list and type(plan.get('closures')) is list)
        refs = set()
        for record in plan['context']:
            validate_record(record, state)
            require(record['restaurant_id'] == restaurant['id'] and record['reference'] not in refs)
            refs.add(record['reference'])
            current = state['reservations'].get(record['reference'])
            require(current is not None and all(record[k] == current[k] for k in ('reservation_id', 'user_id', 'created_at', 'restaurant_id')))
            validate_historical_response(state, record)
        for c in plan['closures']:
            require(c in state['closures'] and c['plan_id'] != pid)
        considered, assignments, moved, unused = planner.solve(restaurant, plan['context'], plan['closures'], dict(proposed, restaurant_id=restaurant['id']))
        require(canonical(considered) == canonical(plan['before']))
        require(canonical(assignments) == canonical(preview.get('assignments')))
        require(type(preview.get('moved_count')) is int and preview['moved_count'] == moved)
        require(type(preview.get('unused_seats')) is int and preview['unused_seats'] == unused)
        require(plan['applied'] == (pid in applied))
        apply_receipts = [r for r in state['receipts'] if type(r) is dict and r.get('path') == '/restaurants/' + restaurant['id'] + '/replans/' + pid + '/apply']
        require(len(apply_receipts) == int(plan['applied']))
        for record, assignment in zip(plan['before'], assignments):
            entries = state['histories'][record['reference']]
            matching = [e for e in entries if e.get('plan_id') == pid]
            if plan['applied'] and assignment['changed']:
                require(len(matching) == 1)
                entry = matching[0]
                require(entry['event'] == 'reassigned' and entry['revision'] == record['revision'] + 1)
                require(entry['changes'] == [{'field': 'table_ids', 'from': record['table_ids'], 'to': assignment['table_ids']}])
            else:
                require(not matching)
        require(any(type(r) is dict and r.get('path') == '/restaurants/' + restaurant['id'] + '/replans'
                    and canonical(r.get('response')) == canonical(preview) for r in state['receipts']))
    for entries in state['histories'].values():
        for entry in entries:
            if entry['event'] == 'reassigned':
                require(entry.get('plan_id') in applied)


def validate_stage4_receipt(state, receipt):
    from .state import require
    from .replans import closure
    from .reservations import restaurant_for
    from .validation import canonical
    path = receipt['path']
    match = re.fullmatch(r'/restaurants/([^/]+)/replans(?:/([^/]+)/apply)?', path)
    if match:
        rid = unquote(match[1])
        restaurant = restaurant_for(state, rid)
        require(receipt['user_id'] in restaurant.get('manager_user_ids', []))
        value = receipt['response']
        pid = value.get('plan_id')
        require(type(pid) is str and pid in state['plans'])
        plan = state['plans'][pid]
        require(plan['restaurant_id'] == rid)
        if match[2] is None:
            require(canonical(value) == canonical(plan['preview']))
            require(closure(restaurant, receipt['body']) == plan['preview']['closure'])
        else:
            require(unquote(match[2]) == pid and plan['applied'])
            require(type(value.get('restaurant_revision')) is int and value['restaurant_revision'] == plan['preview']['restaurant_revision'] + 1)
            records = value.get('reservations')
            require(type(records) is list and len(records) == len(plan['before']))
            for record, before, assignment in zip(records, plan['before'], plan['preview']['assignments']):
                checked_public(state, record, before['user_id'])
                require(record['reference'] == before['reference'] and record['revision'] == before['revision'] + int(assignment['changed']))
                require(record['table_ids'] == assignment['table_ids'])
                require(all(record[k] == before[k] for k in ('starts_at_local', 'starts_at', 'ends_at', 'party_size', 'accepted_terms')))
        return True
    match = re.fullmatch(r'/series/([^/]+)/amend', path)
    if match:
        sid = unquote(match[1])
        require(sid in state['series'] and state['series'][sid]['user_id'] == receipt['user_id'])
        require(any(op['series_id'] == sid and canonical(op['body']) == canonical(receipt['body'])
                    and canonical(op['after']) == canonical(receipt['response']) for op in state['series_operations']))
        return True
    return False
