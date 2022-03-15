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
    assert 'meta' in template, 'template must have section "meta"'
    return template


def _get_runtime_parameters(build_cf, method):
    if build_cf[method]['type'] in {'script', 'file'}:
        return build_cf[method].get('runtime', [])
    elif build_cf[method]['type'] == 'sequence':
        output = {}
        for submethod in build_cf[method]['content']:
            output.update(_get_runtime_parameters(build_cf, submethod))
        return output
    else:
        raise ValueError(f'cant get runtime parameters for {build_cf[method]["type"]}')


def call_template(template, method, params, meta, runtime=None, on_up=False):
    """
    Call template with parameters.

    :param template: Loaded template dictionary.
    :param method: Name of build to run.
    """

    if runtime is None:
        runtime = {}

    assert set(params.keys()) == set(template['params']), \
        missing_msg(set(params.keys()), set(template['params']))

    runtime_parameters = _get_runtime_parameters(template['builds'], method)
    if not set(runtime.keys()).issubset(set(runtime_parameters)):
        raise Exception(f'specified runtime parameters {list(runtime.keys())}'
                        f' don\'t match required {list(runtime_parameters)}')

    def build_method(method):
        cf = template['builds'][method]
        values = get_or_create_values(template, params, meta, on_up=on_up)

        deploy_dir = f'{meta["subdir"]}/tasks'
        if not os.path.exists(deploy_dir):
            os.makedirs(deploy_dir, exist_ok=True)

        if cf['type'] != 'sequence':
            print(f'building "{method}"')
            runtime_defaults = cf.get('runtime', {})
            runtime_defaults.update(runtime)

            content = Template(cf['content'], undefined=StrictUndefined).render(
                params=params, values=values, meta=meta, config=template.get('config', {}),
                runtime=runtime_defaults,
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