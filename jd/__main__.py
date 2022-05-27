import os

import click
import re
from jd.controller import build as _build, rm as _rm, ls as _ls, view as _view


@click.group()
def cli():
    ...


def parse_inputs(x):
    groups = re.finditer('"([^\']+)"', x)
    reference = {}
    for i, g in enumerate(groups):
        x = x.replace(g.group(), f'#{i}')
        reference[f'#{i}'] = g.groups()[0]
    my_dict = dict([x.split('=') for x in x.split(',')])
    for k, val in my_dict.items():
        if val.isnumeric():
            my_dict[k] = eval(val)
        elif val.startswith('#'):
            my_dict[k] = reference[val]
        elif val in {'true', 'True', 'false', 'False'}:
            my_dict[k] = val.lower() == 'true'
        elif '+' in val:
            val = val.split('+')
            val = [x for x in val if x]
            val = [eval(x) if x.isnumeric() else x for x in val]
            my_dict[k] = val
    return my_dict


class KeyValuePairs(click.ParamType):
    """Convert to key value pairs"""
    name = "key-value-pairs"

    def convert(self, value, param, ctx):
        """
        Convert to key value pairs

        :param value: value
        :param param: parameter
        :param ctx: context
        """
        if not value.strip():
            return {}
        try:
            my_dict = parse_inputs(value)
            for k, v in my_dict.items():
                if isinstance(v, str) and '$' in v:
                    group = re.match('.*\$([A-Za-z\_0-9]+)', v).groups()[0]
                    try:
                        my_dict[k] = v.replace(f'${group}', os.environ[group])
                    except KeyError:
                        raise Exception('key values referred to environment variable which did'
                                        ' not exist')
            return my_dict
        except TypeError:
            self.fail(
                "expected string for key-value-pairs() conversion, got "
                f"{value!r} of type {type(value).__name__}",
                param,
                ctx,
            )
        except ValueError:
            self.fail(f"{value!r} is not a valid key-value-pair", param, ctx)


@cli.command()
@click.option('--template', default=None, help='type of resource to list')
@click.option('--root', default='', help='limit list to directory root')
@click.option('--query', default=None, type=KeyValuePairs())
def ls(template, root, query):
    _ls(template, root, query=query)


@cli.command()
@click.option('--id', default=None)
@click.option('--query', default=None, type=KeyValuePairs())
def view(id, query):
    _view(id=id, query=query)


@cli.command()
@click.argument('id')
@click.option('--force/--no-force', default=False, help='force remove even if not stopped')
def rm(id, force):
    _rm(id, force)


@cli.command(help='build template')
@click.argument('method')
@click.option('--template', default=None)
@click.option('--id', default=None)
@click.option('--params', default=None, help='key-value pairs to add to build',
              type=KeyValuePairs())
@click.option('--query', default=None, type=KeyValuePairs())
@click.option('--runtime', default=None, help='runtime key-value pairs to add to build',
              type=KeyValuePairs())
@click.option('--root', default='')
def build(method, template, id, params, runtime, root, query):
    print(params)
    if params is None:
        params = {}
    if isinstance(template, str) and template.endswith('.yaml'):
        template = template.split('.yaml')[0]
    _build(template, method, id=id, root=root, params=params, runtime=runtime, query=query)


if __name__ == '__main__':
    cli()