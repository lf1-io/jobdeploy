import os

from jinja2 import Template, StrictUndefined
import yaml

from jd.values import get_or_create_values
from jd.resources import load_resource
from jd.utils import missing_msg, call_script, log_content


def get_path(id):
    return load_resource(id)['template']


def load_template(path):
    """
    Load deployment template.

    :params path: Load template from path. If templte has "parents" field, then combine with parent
        templates. Parameters named in binds are set in the parents as defaults.
    """
    if not path.endswith('.yaml'):
        path += '.yaml'
    with open('templates/' + path) as f:
        template = yaml.safe_load(f.read())

    assert 'builds' in template, 'template must have section "builds"'
    assert 'params' in template, 'template must have section "params"'
    assert 'config' in template, 'template must have section "config"'
    assert 'meta' in template, 'template must have section "meta"'
    return template


def call_template(template, method, params, meta, on_up=False):
    """
    Call template with parameters.

    :param template: Loaded template dictionary.
    :param method: Name of build to run.
    """

    assert set(params.keys()) == set(template['params']), \
        missing_msg(set(params.keys()), set(template['params']))

    def build_method(method):
        cf = template['builds'][method]
        values = get_or_create_values(template, params, meta, on_up=on_up)

        deploy_dir = f'{meta["subdir"]}/tasks'
        if not os.path.exists(deploy_dir):
            os.makedirs(deploy_dir, exist_ok=True)

        if cf['type'] != 'sequence':
            print(f'building "{method}"')

            content = Template(cf['content'], undefined=StrictUndefined).render(
                params=params, values=values, meta=meta, config=template['config'],
            )
            log_content(content)
            if cf['type'] == 'file':
                path = f'{deploy_dir}/{method}'
                with open(path, 'w') as f:
                    f.write(content)
            if cf['type'] == 'script':
                path = f'{deploy_dir}/{method}'
                exit_code = call_script(path, content, grab_output=False, cleanup=False)
                if exit_code and exit_code not in cf.get('whitelist', []):
                    raise Exception(f'script exited with non-zero exit code: {exit_code}.')
            return

        for m in cf['content']:
            build_method(m)

    build_method(method)