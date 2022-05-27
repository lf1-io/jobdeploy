import os
import time

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

    :params path: Load template from path. If template has "parents" field, then combine with parent
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


class TemplateCaller:
    def __init__(self, template, params, meta):
        assert set(params.keys()) == set(template['params']), \
            missing_msg(set(params.keys()), set(template['params']))
        self.params = params
        self.template = template
        self.meta = meta
        self.deploy_dir = f'{meta["subdir"]}/tasks'
        if not os.path.exists(self.deploy_dir):
            os.makedirs(self.deploy_dir, exist_ok=True)

    def _get_values(self, on_up=False):
        return get_or_create_values(self.template, self.params, self.meta, on_up=on_up)

    def __call__(self, method, runtime=None, on_up=False):
        print('-' * 20 + '\n' + f'BUILDING {method}\n' + '-' * 20)
        cf = self.template['builds'][method]
        runtime_parameters = _get_runtime_parameters(self.template['builds'], method)
        if not set(runtime.keys()).issubset(set(runtime_parameters)):
            raise Exception(f'specified runtime parameters {list(runtime.keys())}'
                            f' don\'t match required {list(runtime_parameters)}')
        runtime_defaults = cf.get('runtime', {})
        runtime_defaults.update(runtime)

        if cf['type'] == 'sequence':
            for method in cf['content']:
                self(method, runtime=runtime_defaults, on_up=on_up)
        else:
            if cf['type'] == 'file':
                self._do_file(cf, method, on_up, runtime_defaults)
            elif cf['type'] == 'script':
                self._do_script(cf, method, on_up, runtime_defaults)
            else:
                raise ValueError(f'Unknown build type {type}')

    def _get_content(self, content, runtime_defaults, on_up=False):
        return Template(content, undefined=StrictUndefined).render(
            params=self.params,
            values=self._get_values(on_up=on_up),
            meta=self.meta,
            config=self.template.get('config', {}),
            runtime=runtime_defaults,
        )

    def _do_file(self, cf, method, on_up, runtime_defaults):
        content = self._get_content(cf['content'], runtime_defaults=runtime_defaults,
                                    on_up=on_up)
        log_content(content)
        path = f'{self.deploy_dir}/{method}'
        with open(path, 'w') as f:
            f.write(content)

    def _do_script(self, cf, method, on_up, runtime_defaults):
        num_retries = cf.get('num_retries', 0)
        while True:
            try:
                self._execute_script(cf, method, on_up, runtime_defaults)
                return
            except Exception as e:
                if num_retries == 0:
                    raise e
                num_retries -= 1
                print(f'couldn\'t execute retrying... {str(e)}')
                time.sleep(cf.get('retry_interval', 10))

    def _execute_script(self, cf, method, on_up, runtime_defaults):
        content = self._get_content(cf['content'], runtime_defaults=runtime_defaults,
                                    on_up=on_up)
        path = f'{self.deploy_dir}/{method}'
        exit_code = call_script(path, content, grab_output=False, cleanup=False)
        if exit_code and exit_code not in cf.get('whitelist', []):
            raise Exception(f'script exited with non-zero exit code: {exit_code}.')
