import datetime
import json
import os

from jd.resources import load_resource, load_all_resources
from jd.utils import random_id
from jd.utils import missing_msg
from jd.templates import call_template, load_template, get_path


def get_project():
    return os.getcwd().split('/')[-1]


def prepare_params_for_resource(path, template, params):
    meta = {}
    meta['id'] = random_id()
    meta['commit'] = os.popen('git rev-parse HEAD').read().split('\n')[0]
    msg = os.popen('git log -1 --pretty=%B').read().split('\n')[0]
    meta['message'] = '\n'.join([x.strip() for x in msg.split('\n') if x.strip()])
    if not meta['commit']:
        raise Exception('something went wrong determining the current commit')
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


def rm(id, purge=False, down=True):
    r = load_resource(id)
    if down:
        if 'stopped' not in r:
            build(r['template'], 'down', id=id)
    if purge:
        build(r['template'], 'purge', id=id)

    os.system(f'rm -rf .jd/{r["subdir"]}')


def ls(template=None):
    out = load_all_resources()
    out = [{k: v for k, v in x.items() if k not in {'values', 'config'}} for x in out]
    if template is not None:
        out = [x for x in out if x['template'] == template]
    print(json.dumps(out, indent=2))
    return out


def view(id):
    out = load_resource(id)
    print(json.dumps(out, indent=2))


def _get_last_id(template_path):
    records = ls(template=template_path)
    return records[-1]['id']


def build(path, method, id=None, **params):
    """ Call template located at "path" with parameters.

    :param path: Template .yaml path.
    :param method: Name of build to run.
    :param params: Run-time parameters (key values)
    """

    if id is None:
        id = _get_last_id(path)
    if path is None:
        path = get_path(id=id)
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
        call_template(template, method, params, meta, on_up=method == 'up')

        if method == 'down':
            postprocess_params_for_resource(info)

    except Exception as e:
        if method == 'up':
            os.system(f'rm -rf .jd/{info["subdir"]}')
        raise e

