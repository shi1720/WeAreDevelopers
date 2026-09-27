"""Shared wire validation and explicit API failures."""
import json
import math
import re
from datetime import date


class APIError(Exception):
    def __init__(self, status, code, message=None):
        self.status = status
        self.code = code
        self.message = message or code.replace('_', ' ')
        super().__init__(self.message)


def invalid(message='Invalid value'):
    raise APIError(422, 'validation_failed', message)


def object_body(raw):
    def number(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError('Non-finite JSON number')
        return parsed

    def constant(_):
        raise ValueError('Invalid JSON constant')

    try:
        value = json.loads(raw, parse_constant=constant, parse_float=number)
    except (ValueError, UnicodeError):
        raise APIError(400, 'malformed_request') from None
    if not isinstance(value, dict):
        raise APIError(400, 'malformed_request', 'Expected a JSON object')
    return value


def field(body, name, kind=str, required=True):
    if name not in body:
        if required:
            invalid('Missing ' + name)
        return None
    value = body[name]
    if type(value) is not kind:
        raise APIError(400, 'malformed_request', 'Wrong type for ' + name)
    return value


def identifier(body, name, required=True):
    value = field(body, name, required=required)
    if value is not None and (not value or len(value) > 64):
        invalid('Invalid ' + name)
    return value


def party_size(value):
    if type(value) is not int or value < 1:
        invalid('Party size must be a positive integer')
    return value


def calendar_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value, re.ASCII):
        invalid('Expected YYYY-MM-DD')
    try:
        return date.fromisoformat(value)
    except ValueError:
        invalid('Invalid calendar date')


def canonical(value):
    # JSON booleans and numbers must remain distinct (Python equality conflates them).
    # Numeric spelling, whitespace and object ordering do not affect JSON values.
    def normalize(item):
        if type(item) is dict:
            return ['object', [[k, normalize(v)] for k, v in sorted(item.items())]]
        if type(item) is list:
            return ['array', [normalize(v) for v in item]]
        if type(item) in (int, float):
            return ['number', item]
        return [type(item).__name__, item]
    return normalize(value)
