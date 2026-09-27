"""Manager previews and atomic applications, preserving accepted promises."""
from copy import deepcopy
from datetime import datetime
import re
import secrets
from .validation import APIError, identifier, invalid
from . import planner, reservations, history, series


def manager(state, user, rid):
    restaurant = reservations.restaurant_for(state, rid)
    if user not in restaurant.get('manager_user_ids', []):
        raise APIError(403, 'forbidden')
    return restaurant


def closure(restaurant, body):
    tid = identifier(body, 'table_id')
    if tid not in {t['id'] for t in restaurant['tables']}:
        raise APIError(404, 'not_found')
    for name in ('from', 'to'):
        value = body.get(name)
        if type(value) is not str or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})', value, re.ASCII):
            invalid('Closure instants require explicit offsets')
        try:
            datetime.fromisoformat(value)
        except ValueError:
            invalid('Invalid closure instant')
    try:
        start, end = planner.interval(body['from'], body['to'])
    except (ValueError, OverflowError):
        invalid('Invalid closure interval')
    if start >= end:
        invalid('Closure must have positive duration')
    return {k: body[k] for k in ('table_id', 'from', 'to')}


def preview(state, user, rid, body):
    restaurant = manager(state, user, rid)
    proposed = closure(restaurant, body)
    considered, assignments, moved, unused = planner.solve(restaurant, list(state['reservations'].values()), state['closures'], dict(proposed, restaurant_id=rid))
    pid = 'plan_' + secrets.token_hex(16)
    result = {'plan_id': pid, 'restaurant_revision': state['restaurant_revisions'][rid],
              'closure': proposed, 'assignments': assignments, 'moved_count': moved, 'unused_seats': unused}
    state['plans'][pid] = {'restaurant_id': rid, 'preview': deepcopy(result), 'applied': False,
                          'before': deepcopy(considered),
                          'context': deepcopy([r for r in state['reservations'].values() if r['restaurant_id'] == rid and r['status'] == 'confirmed']),
                          'closures': deepcopy(state['closures'])}
    return result


def get(state, user, rid, pid):
    manager(state, user, rid)
    plan = state['plans'].get(pid)
    if plan is None or plan['restaurant_id'] != rid:
        raise APIError(404, 'not_found')
    return plan


def detail(state, user, rid, pid):
    plan = get(state, user, rid, pid)
    return dict(deepcopy(plan['preview']), before_reservations=[reservations.public(r) for r in plan['before']])


def apply(state, user, rid, pid):
    plan = get(state, user, rid, pid)
    if plan['applied']:
        raise APIError(409, 'plan_already_applied')
    if plan['preview']['restaurant_revision'] != state['restaurant_revisions'][rid]:
        raise APIError(409, 'stale_plan')
    changed = []
    for assignment in plan['preview']['assignments']:
        if not assignment['changed']:
            continue
        ref = assignment['reference']
        record = state['reservations'][ref]
        before = deepcopy(record)
        record['table_ids'] = list(assignment['table_ids'])
        record.pop('table_id', None)
        if len(record['table_ids']) == 1:
            record['table_id'] = record['table_ids'][0]
        record['revision'] += 1
        history.append(state, record, 'reassigned', before)
        entry = state['histories'][ref][-1]
        entry['changes'] = [{'field': 'table_ids', 'from': before['table_ids'], 'to': record['table_ids']}]
        entry['plan_id'] = pid
        changed.append(ref)
    series.touch(state, changed)
    state['closures'].append(dict(plan['preview']['closure'], restaurant_id=rid, plan_id=pid))
    state['restaurant_revisions'][rid] += 1
    plan['applied'] = True
    return {'plan_id': pid, 'restaurant_revision': state['restaurant_revisions'][rid],
            'reservations': [reservations.public(state['reservations'][a['reference']]) for a in plan['preview']['assignments']]}
