import datetime
import json
import os
import random

from templates import call_template, load_template


def random_id():
    """ Random ID identifier."""
    letters = list('ABDEFGHIJKLMNOPQRSTUVWXZYZ0123456789')
    id_ = [random.choice(letters) for _ in range(8)]
    return ''.join(id_)


def build_meta(path, method, **params):
    """
    Call template at "path" with parameters.

    :param path: Template .yaml path.
    :param method: Name of build to run.
    """
    if method != 'up':
        assert set(params.keys()) == {'id'}
    else:
        assert 'id' not in params
        params['id'] = random_id()

    prefix = path.replace('/', '-')
    subdir = prefix + '-' + params['id']

    if method != 'up':
        with open(f'.jd/{subdir}/meta.json') as f:
            meta = json.load(f)
        params.update(meta['params'])

    else:
        params['subdir'] = subdir
        os.system(f'mkdir -p .jd/{params["subdir"]}/tasks')
        try:
            with open('.jd/project.json') as f:
                params.update(json.load(f))
        except FileNotFoundError:
            pass

    template, binds = load_template(path)
    if method == 'up':
        params.update(binds)

    call_template(template, method, **params)

    if method == 'up':
        meta = {'params': params, 'created': str(datetime.datetime.now()), 'template': path}
        with open(f'.jd/{params["subdir"]}/meta.json', 'w') as f:
            json.dump(meta, f)

    if method == 'down':
        meta['stopped'] = str(datetime.datetime.now())
        with open(f'.jd/{params["subdir"]}/meta.json', 'w') as f:
            json.dump(meta, f)
