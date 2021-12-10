import os
import random


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
