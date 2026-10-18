"""Проверка OpenAPI, ссылок, примеров и границ входных схем без сервера."""
from pathlib import Path
import copy
import re

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import validate


ROOT = Path(__file__).resolve().parent
spec = yaml.safe_load((ROOT / 'openapi.yaml').read_text(encoding='utf-8'))
validate(spec)


def resolve(value):
    if isinstance(value, dict):
        if '$ref' in value:
            target = spec
            assert value['$ref'].startswith('#/'), 'Only internal refs are expected'
            for key in value['$ref'][2:].split('/'):
                target = target[key.replace('~1', '/').replace('~0', '~')]
            return resolve({**target, **{k: v for k, v in value.items() if k != '$ref'}})
        return {key: resolve(item) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve(item) for item in value]
    return value


resolved = resolve(spec)
checker = FormatChecker()
example_count = 0


def check_examples(node):
    global example_count
    if isinstance(node, dict):
        if 'schema' in node:
            validator = Draft202012Validator(node['schema'], format_checker=checker)
            if 'example' in node:
                validator.validate(node['example'])
                example_count += 1
            for item in node.get('examples', {}).values():
                validator.validate(item['value'])
                example_count += 1
        for value in node.values():
            check_examples(value)
    elif isinstance(node, list):
        for value in node:
            check_examples(value)


check_examples(resolved)
for schema in resolved['components']['schemas'].values():
    Draft202012Validator.check_schema(schema)

negative_count = 0


def reject(schema_name, value):
    global negative_count
    validator = Draft202012Validator(resolved['components']['schemas'][schema_name], format_checker=checker)
    assert not validator.is_valid(value), f'{schema_name} accepted invalid input: {value}'
    negative_count += 1


def sample(name):
    return copy.deepcopy(resolved['components']['examples'][name]['value'])


for name in ('BookCreate', 'BookUpdate', 'ReaderCreate', 'ReaderUpdate', 'LoanCreate'):
    reject(name, {**sample(name), 'unexpected': True})
    reject(name, {**sample(name), 'id': sample('Book')['id']})
    reject(name, {})

reject('BookCreate', {**sample('BookCreate'), 'available_copies': 2})
reject('BookUpdate', {'available_copies': 2})
reject('BookCreate', {**sample('BookCreate'), 'title': '   '})
reject('BookCreate', {**sample('BookCreate'), 'total_copies': -1})
reject('BookCreate', {**sample('BookCreate'), 'isbn': '1234567890123'})
reject('BookUpdate', {'title': None})
reject('ReaderCreate', {**sample('ReaderCreate'), 'email': 'invalid'})
reject('ReaderCreate', {**sample('ReaderCreate'), 'registered_at': '2026-10-01T00:00:00Z'})
reject('ReaderUpdate', {'full_name': None})
reject('LoanCreate', {**sample('LoanCreate'), 'returned_at': None})
reject('LoanCreate', {**sample('LoanCreate'), 'loaned_at': '2026-10-18T10:00:00Z'})
reject('LoanCreate', {**sample('LoanCreate'), 'book_id': 'not-a-uuid'})
reject('LoanCreate', {**sample('LoanCreate'), 'due_date': '2026-02-30'})
reject('LoanCreate', {**sample('LoanCreate'), 'due_date': None})
reject('Loan', {**sample('Loan'), 'returned_at': 0})

operations = []
for path, item in resolved['paths'].items():
    assert '_' not in path, f'URL must use kebab-case: {path}'
    for method in ('get', 'post', 'patch', 'delete'):
        if method not in item:
            continue
        op = item[method]
        operations.append(op['operationId'])
        assert op['summary'] and op['description']
        assert op['tags'][0] in ('Books', 'Readers', 'Loans')
        assert '401' in op['responses']
        for code, response in op['responses'].items():
            if int(code) >= 400:
                assert response['content']['application/json']['schema'] == resolved['components']['schemas']['ErrorResponse']
            if code == '204':
                assert 'content' not in response

expected = {
    '/books': {'get', 'post'}, '/books/{id}': {'get', 'patch', 'delete'},
    '/readers': {'get', 'post'}, '/readers/{id}': {'get', 'patch', 'delete'},
    '/loans': {'get', 'post'}, '/loans/{id}': {'get'}, '/loans/{id}/return': {'post'},
}
assert set(resolved['paths']) == set(expected)
for path, methods in expected.items():
    assert set(resolved['paths'][path]) - {'parameters'} == methods
assert len(operations) == len(set(operations)) == 14
for path in ('/books', '/readers', '/loans'):
    names = {p['name'] for p in resolved['paths'][path]['get']['parameters']}
    assert {'page', 'page_size', 'sort'} <= names
    assert names - {'page', 'page_size', 'sort'}
for name, schema in resolved['components']['schemas'].items():
    for prop in schema.get('properties', {}):
        assert re.fullmatch(r'[a-z][a-z0-9_]*', prop), (name, prop)
assert spec['servers'][0]['url'].endswith('/v1/')
assert resolved['components']['schemas']['Book']['properties']['available_copies']['readOnly']
assert spec['security'] == [{'BearerAuth': []}]
assert any(p['name'] == 'Idempotency-Key' and p['required'] for p in resolved['paths']['/loans']['post']['parameters'])
isbn = sample('BookCreate')['isbn']
assert sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(isbn)) % 10 == 0

print('PASS: OpenAPI 3.1, all local refs and schemas')
print(f'PASS: {len(operations)} unique operations and required endpoints')
print(f'PASS: {example_count} example occurrences match their schemas')
print(f'PASS: {negative_count} invalid request/response cases rejected')
print('PASS: collections, error envelopes, naming, JWT, ISBN sample and readOnly')
print('NOTE: database rules, UTC comparisons, concurrency and replay require a server; this validates the contract only.')
