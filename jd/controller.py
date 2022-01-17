import datetime
import json
import os
import re

from jd.resources import load_resource, load_all_resources
from jd.utils import random_id
from jd.utils import missing_msg
from jd.templates import call_template, load_template, get_path


def get_project():
    return os.getcwd().split('/')[-1]


def prepare_params_for_resource(path, template, root, params):
    meta = {}
    meta['id'] = random_id()
    meta['commit_up'] = os.popen('git rev-parse HEAD').read().split('\n')[0]
    msg = os.popen('git log -1 --pretty=%B').read().split('\n')[0]
    meta['message_up'] = '\n'.join([x.strip() for x in msg.split('\n') if x.strip()])
    meta['jd_path'] = root + 'jd.json'
    if not meta['commit_up']:
        raise Exception('something went wrong determining the current commit')
    subdir = f'{root}.jd/{meta["id"]}'
    meta['subdir'] = subdir
    os.system(f'mkdir -p {meta["subdir"]}/tasks')
    meta['project'] = get_project()
    assert set(params.keys()) == set(template['params']), \
        missing_msg(set(params.keys()), set(template['params']))

    info = {'params': params,
            'config': template['config'],
            'created': str(datetime.datetime.now()),
            'template': path,
            **meta}

    try:
        with open(f'{meta["jd_path"]}') as f:
            all_jobs = json.load(f)
    except FileNotFoundError:
        all_jobs = []

    all_jobs.append(info)
    with open(f'{meta["jd_path"]}', 'w') as f:
        json.dump(all_jobs, f, indent=2)

    return info


def postprocess_params_for_resource(info, method):
    info['stopped'] = str(datetime.datetime.now())
    if method == 'down':
        info['commit_down'] = os.popen('git rev-parse HEAD').read().split('\n')[0]
        msg = os.popen('git log -1 --pretty=%B').read().split('\n')[0]
        info['message_down'] = '\n'.join([x.strip() for x in msg.split('\n') if x.strip()])
    with open(info['jd_path']) as f:
        jobs = json.load(f)
    jobs = [x if x['id'] != info['id'] else info for x in jobs]
    with open(f'{info["jd_path"]}', 'w') as f:
        json.dump(jobs, f, indent=2)


def rm(id, purge=False, down=True):
    r = load_resource(id)
    if down:
        if 'stopped' not in r:
            build(r['template'], 'down', id=id)
    if purge:
        build(r['template'], 'purge', id=id)

    with open(r['jd_path']) as f:
        jobs = json.load(f)
    jobs = [x for x in jobs if x['id'] != r['id']]

    with open(r['jd_path'], 'w') as f:
        json.dump(jobs, f, indent=2)


def ls(template=None, root=''):
    out = load_all_resources(root=root)
    out = [{k: v for k, v in x.items() if k not in {'values', 'config'}} for x in out]
    if template is not None:
        out = [x for x in out if re.match(template, x['template']) is not None]
    print(json.dumps(out, indent=2))
    return out


def view(id):
    out = load_resource(id)
    print(json.dumps(out, indent=2))


def _get_last_id(template_path):
    records = ls(template=template_path)
    return records[-1]['id']


def _get_jd_path(id):
    records = ls()
    return next(x for x in records if x['id'] == id)['jd_path']


def build(path, method, id=None, root='', **params):
    """ Call template located at "path" with parameters.

    :param path: Template .yaml path.
    :param method: Name of build to run.
    :param root: Root directory for storing meta-data
    :param params: Run-time parameters (key values)
    """

    if id is None and not (method == 'up'):
        id = _get_last_id(path)
    if path is None:
        path = get_path(id=id)
    template = load_template(path)
    if root and root[-1] != '/':
        root = root.strip() + '/'

    try:
        if method == 'up':
            if not os.path.exists(root + '.jd'):
                os.makedirs(root + '.jd')
            info = prepare_params_for_resource(path, template, root, params)
        else:
            jd_path = _get_jd_path(id)
            assert id is not None
            with open(jd_path) as f:
                jobs = json.load(f)
            info = next(j for j in jobs if j['id'] == id)
            params = info['params']

        meta = {k: v for k, v in info.items() if k not in {'values', 'params', 'config'}}
        call_template(template, method, params, meta, on_up=method == 'up')

        if method == 'down':
            postprocess_params_for_resource(info, method)

    except Exception as e:
        # if method == 'up':
        #     rm(info['id'], down=False, purge=False)
        pass
        raise e

