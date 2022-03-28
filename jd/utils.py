import os
import random


def evaluate_query(r, query):
    """
    >>> r = {"id": "123", "info": {"name": "bla"}}
    >>> evaluate_query(r, {"id": "123"})
    True
    >>> evaluate_query(r, {"info.name": "bla"})
    True
    >>> evaluate_query(r, {"info.name": "foo"})
    False
    """
    if len(query) > 1:
        return all([evaluate_query(r, {k: v}) for k, v in query.items()])
    key = next(iter(query.keys()))
    value = next(iter(query.values()))
    if '.' in key:
        root = key.split('.')[0]
        previous = '.'.join(key.split('.')[1:])
        if root not in r:
            return False
        return evaluate_query(r[root], {previous: value})
    try:
        return r[key] == value
    except KeyError:
        return False


def missing_msg(params, target):
    msg = ''
    if not params.issubset(target):
        msg += f'unexpected values in input: {params - target}; '
    if not target.issubset(params):
        msg += f'missing values in input: {target - params}'
    return msg


def random_id():
    """ Random ID identifier."""
    letters = list('ABDEFGHIJKLMNOPQRSTUVWXZYZ0123456789')
    id_ = [random.choice(letters) for _ in range(8)]
    return ''.join(id_)


def call_script(path, content, grab_output=False, cleanup=False):
    with open(path, 'w') as f:
        f.write(content)
    os.system(f'chmod +x {path}')
    if grab_output:
        output = os.popen(path).read()[:-1]
        if not output:
            raise Exception('grabbing output failed.')
    else:
        output = os.system(path)
    if cleanup:
        os.system(f'rm {path}')
    return output


def log_content(content):
    lines = content.split('\n')
    len_ = max([len(x) for x in lines])
    print(f'content:\n  ' + len_ * '-')
    print('\n'.join(['  ' + x for x in lines]))
    print(f'  ' + len_ * '-')
