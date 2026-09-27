"""Append-only histories retain the terms in force at each accepted change."""
from copy import deepcopy
from datetime import datetime, timezone


def changes(before, after):
    old_ids = before['table_ids'] if before else None
    ids = after['table_ids']
    result = []
    if old_ids != ids:
        if len(ids) == 1 and (old_ids is None or len(old_ids) == 1):
            result.append({'field': 'table_id', 'from': old_ids[0] if old_ids else None, 'to': ids[0]})
        else:
            result.append({'field': 'table_ids', 'from': deepcopy(old_ids), 'to': deepcopy(ids)})
    for name in ('starts_at_local', 'party_size'):
        old = before[name] if before else None
        if old != after[name]:
            result.append({'field': name, 'from': old, 'to': after[name]})
    return result


def append(state, record, event, before=None, at=None):
    entries = state['histories'].setdefault(record['reference'], [])
    timestamp = at or datetime.now(timezone.utc).isoformat()
    if entries and datetime.fromisoformat(timestamp) < datetime.fromisoformat(entries[-1]['at']):
        timestamp = entries[-1]['at']
    entries.append({'seq': len(entries) + 1, 'at': timestamp, 'event': event,
        'changes': [] if event == 'cancelled' else changes(before, record),
        'revision': record['revision'], 'accepted_terms': deepcopy(record['accepted_terms'])})


def initialize(state, record):
    append(state, record, 'created', at=record['created_at'])
