import datetime
import json
import os

from utils import random_id
from utils import missing_msg
from templates import call_template, load_template, get_path


def get_project():
    return os.getcwd().split('/')[-1]


def prepare_params_for_resource(path, template, params):
    meta = {}
    meta['id'] = random_id()
    prefix = path.replace('/', '-')
    subdir = prefix + '-' + meta['id']

    meta['subdir'] = subdir
    os.system(f'mkdir -p .jd/{meta["subdir"]}/tasks')
    meta['project'] = get_project()
    assert set(params.keys()) == set(template['params']), \
        missing_msg(set(params.keys()), set(template['params']))

    info = {'params': params,
            'config': template['config'],
            'created': str(datetime.datetime.now()),
            'template': path,
            **meta}

    with open(f'.jd/{meta["subdir"]}/info.json', 'w') as f:
        json.dump(info, f)

    return info


def postprocess_params_for_resource(info):
    info['stopped'] = str(datetime.datetime.now())
    with open(f'.jd/{info["subdir"]}/info.json', 'w') as f:
        json.dump(info, f)


def build_meta(path, method, id=None, **params):
    """ Call template located at "path" with parameters.

    :param path: Template .yaml path.
    :param method: Name of build to run.
    :param params: Run-time parameters (key values)
    """

    if path is None:
        path = get_path(id=params['id'])
    template = load_template(path)

    try:
        if method == 'up':
            info = prepare_params_for_resource(path, template, params)
        else:
            assert id is not None
            with open(f'.jd/{path.replace("/", "-")}-{id}/info.json') as f:
                info = json.load(f)
            params = info['params']

        meta = {k: v for k, v in info.items() if k not in {'values', 'params', 'config'}}
        call_template(template, method, params, meta)

        if method == 'down':
            postprocess_params_for_resource(info)

    except Exception as e:
        if method == 'up':
            os.system(f'rm -rf .jd/{info["subdir"]}')
        raise e

