import click
import json
import os

from controller import build_meta
from resources import load_all_resources, load_resource


@click.group()
def cli():
    ...


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
            my_dict = dict([x.split('=') for x in value.split(',')])
            for k, val in my_dict.items():
                if val.isnumeric():
                    my_dict[k] = eval(val)
                elif val in {'true', 'True', 'false', 'False'}:
                    my_dict[k] = val.lower == 'true'
                elif '+' in val:
                    val = val.split('+')
                    val = [x for x in val if x]
                    val = [eval(x) if x.isnumeric() else x for x in val]
                    my_dict[k] = val
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
def ls():
    print(json.dumps(load_all_resources(), indent=2))


@cli.command()
@click.argument('id')
@click.option('--purge/--no-purge', default=False, help='purge resource')
def rm(id, purge):
    r = load_resource(id)
    if 'stopped' not in r:
        build_meta(r['template'], 'down', id=id)
    if purge:
        build_meta(r['template'], 'purge', id=id)

    os.system(f'rm -rf .jd/{r["params"]["subdir"]}')


@cli.command(help='build template')
@click.argument('template')
@click.argument('method')
@click.option('--kwargs', default=None, help='key-value pairs to add to build',
              type=KeyValuePairs())
def build(template, method, kwargs):
    print(kwargs)
    if kwargs is None:
        kwargs = {}
    if template.endswith('.yaml'):
        template = template.split('.yaml')[0]
    build_meta(template, method, **kwargs)


if __name__ == '__main__':
    cli()
