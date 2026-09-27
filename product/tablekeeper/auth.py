"""Password hashing and non-expiring opaque sessions."""
import hashlib
import hmac
import secrets
import re
from .validation import APIError, field, invalid


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return {'algorithm': 'scrypt', 'salt': salt, 'digest': digest}


def valid_hash(value):
    return (isinstance(value, dict) and value.get('algorithm') == 'scrypt'
            and isinstance(value.get('salt'), str)
            and re.fullmatch('[0-9a-f]{32}', value['salt']) is not None
            and isinstance(value.get('digest'), str)
            and re.fullmatch('[0-9a-f]{128}', value['digest']) is not None)


def check_password(password, stored):
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(stored['salt']), n=16384, r=8, p=1).hex()
    return hmac.compare_digest(digest, stored['digest'])


def email_value(body):
    email = field(body, 'email')
    if not re.fullmatch(r'[^\s@]+@[^\s@]+', email):
        invalid('Expected local@domain email')
    return email


def authenticate(state, header):
    if not isinstance(header, str) or not re.fullmatch(r'Bearer [^\s]+', header):
        raise APIError(401, 'unauthenticated')
    uid = state['tokens'].get(header[7:])
    if uid is None:
        raise APIError(401, 'unauthenticated')
    return uid


def session(state, user):
    token = secrets.token_urlsafe(32)
    state['tokens'][token] = user['id']
    return {'user_id': user['id'], 'display_name': user['display_name'], 'token': token}


def signup(state, body):
    email = email_value(body)
    password = field(body, 'password')
    name = field(body, 'display_name')
    if len(password) < 8:
        invalid('Password must contain at least eight characters')
    if any(u['email'] == email for u in state['users'].values()):
        raise APIError(409, 'email_taken')
    uid = 'u_' + secrets.token_hex(16)
    user = {'id': uid, 'email': email, 'display_name': name, 'password_hash': hash_password(password)}
    state['users'][uid] = user
    return session(state, user)


def login(state, body):
    email = field(body, 'email')
    password = field(body, 'password')
    user = next((u for u in state['users'].values() if u['email'] == email), None)
    if user is None or not check_password(password, user['password_hash']):
        raise APIError(401, 'unauthenticated')
    return session(state, user)
