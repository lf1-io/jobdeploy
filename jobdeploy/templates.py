import json

from jinja2 import Template, StrictUndefined
import os
import yaml


def load_template(path):
    """
    Load deployment template.

    :params path: Load template from path. If template has "parent" field, then combine with parent
        template. Parameters named in binds are set in the parent by default.
    """
    with open(path + '.yaml') as f:
        template = yaml.safe_load(f.read())
    if not 'parent' in template:
        return template
    with open(template['parent']) as f:
        parent = yaml.safe_load(f.read())
    binds = template.get('binds', {})
    parent['params'].extend([x for x in template.get('params', []) if x not in parent['params']])
    for k in template.get('builds', {}):
        parent['builds'][k] = template['builds'][k]
    return parent, binds


def create_value(value, other_values, params):
    """
    Format a value using template parameters.

    :param value: Value to be formatted using Jinja2.
    :param other_values: Other pre-built values to be used in the value with {{ values[...] }}.
    :param params: Dictionary of parameters, referred to by {{ params[...] }}.
    """
    if isinstance(value, str):
        return Template(value, undefined=StrictUndefined).render(params=params,
                                                                 values=other_values)
    elif isinstance(value, list):
        return [create_value(x, other_values, params) for x in value]

    elif isinstance(value, dict):
        return {k: create_value(value[k], other_values, params) for k in value}

    else:
        raise NotImplementedError('only strings, and recursively lists and dicts supported')


def create_values(values, **params):
    """
    Create values. Go through dictionary of values based on parameters dictionary.

    :param values: Dictionary of values with Jinja2 variables in strings.
    """
    out = {}
    for k in values:
        out[k] = create_value(values[k], out, params)
    return out


def call_template(template, method, **params):
    """
    Call template with parameters.

    :param template: Loaded template dictionary.
    :param method: Name of build to run.
    """

    assert set(params.keys()) == set(template['params']), \
        (f'missing keys: {set(template["params"]) - set(params.keys())}; '
         f'unexpected keys: {set(params.keys()) - set(template["params"])}')

    def build_method(method):
        cf = template['builds'][method]
        if method == 'up' and 'values' in template:
            values = create_values(template, **params)
            with open(params['subdir'] + '/values.json', 'w') as f:
                json.dump(values, f)
        else:
            try:
                with open(params['subdir'] + '/values.json') as f:
                    values = json.load(f)
            except FileNotFoundError:
                values = {}
        if cf['type'] != 'sequence':
            print(f'building "{method}"')

            content = Template(cf['content'], undefined=StrictUndefined).render(
                params=params, values=values,
            )
            lines = content.split('\n')
            len_ = max([len(x) for x in lines])
            print(f'content:\n  ' + len_ * '-')
            print('\n'.join(['  ' + x for x in lines]))
            print(f'  ' + len_ * '-')
            if cf['type'] == 'file':
                path = f'.jd/{params["subdir"]}/tasks/{method}'
                with open(path, 'w') as f:
                    f.write(content)
            if cf['type'] == 'script':
                path = f'.jd/{params["subdir"]}/tasks/{method}'
                with open(path, 'w') as f:
                    f.write(content)
                os.system(f'chmod +x {path}')
                exit_code = os.system(f'./{path}')
                if exit_code and exit_code not in cf.get('whitelist', []):
                    raise Exception(f'script exited with non-zero exit code: {exit_code}.')
            return

        for m in cf['content']:
            build_method(m)

    build_method(method)

