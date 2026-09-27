"""Immutable dated policies and accepted-term snapshots."""
from copy import deepcopy
import re
from .validation import APIError, calendar_date, invalid

FIELDS = ('slot_minutes', 'reservation_duration_minutes', 'cancellation_cutoff_minutes', 'opening_hours', 'capacities')


def base_terms(restaurant):
    return {'policy_version': 0, **{k: deepcopy(restaurant[k]) for k in FIELDS[:-1]},
            'capacities': {t['id']: t['capacity'] for t in restaurant['tables']}}


def select_terms(state, restaurant, local_date):
    calendar_date(local_date)
    eligible = [p for p in state['policies'][restaurant['id']] if p['effective_from'] <= local_date]
    if not eligible:
        return base_terms(restaurant)
    selected = max(eligible, key=lambda p: (p['effective_from'], p['policy_version']))
    return {k: deepcopy(v) for k, v in selected.items() if k != 'effective_from'}


def effective_restaurant(restaurant, terms):
    result = deepcopy(restaurant)
    for key in FIELDS[:-1]:
        result[key] = deepcopy(terms[key])
    for table in result['tables']:
        table['capacity'] = terms['capacities'][table['id']]
    result['policy_version'] = terms['policy_version']
    return result


def validate_policy(restaurant, body):
    if type(body) is not dict:
        invalid('Expected a complete policy')
    calendar_date(body.get('effective_from'))
    for name, low, high in [('slot_minutes', 1, 1440), ('reservation_duration_minutes', 1, 1440),
                            ('cancellation_cutoff_minutes', 0, 10080)]:
        value = body.get(name)
        if type(value) is not int or not low <= value <= high:
            invalid('Invalid ' + name)
    hours = body.get('opening_hours')
    if type(hours) is not list:
        invalid('Invalid opening_hours')
    seen = set()
    for h in hours:
        if type(h) is not dict or type(h.get('weekday')) is not str or h['weekday'] not in ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun') or h['weekday'] in seen:
            invalid('Invalid weekday')
        seen.add(h['weekday'])
        for name in ('opens', 'closes'):
            if type(h.get(name)) is not str or not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', h[name]):
                invalid('Invalid opening time')
        if h['closes'] <= h['opens']:
            invalid('Opening hours must end on the same day')
    capacities = body.get('capacities')
    if type(capacities) is not dict or set(capacities) != {t['id'] for t in restaurant['tables']}:
        invalid('Supply every table capacity')
    if any(type(v) is not int or not 1 <= v <= 100 for v in capacities.values()):
        invalid('Invalid capacity')
    result = {k: deepcopy(body[k]) for k in ('effective_from',) + FIELDS}
    result['opening_hours'] = [{k: h[k] for k in ('weekday', 'opens', 'closes')} for h in hours]
    return result


def publish(state, user, restaurant, body):
    if user not in restaurant.get('manager_user_ids', []):
        raise APIError(403, 'forbidden')
    result = validate_policy(restaurant, body)
    result['policy_version'] = len(state['policies'][restaurant['id']]) + 1
    state['policies'][restaurant['id']].append(result)
    state['restaurant_revisions'][restaurant['id']] += 1
    return deepcopy(result)
