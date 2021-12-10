import click
from controller import build as _build, rm as _rm, ls as _ls


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
@click.option('--template', default=None, help='type of resource to list')
def ls(template):
    _ls(template)


@cli.command()
@click.argument('id')
@click.option('--purge/--no-purge', default=False, help='purge resource')
def rm(id, purge):
    _rm(id, purge)


@cli.command(help='build template')
@click.argument('method')
@click.option('--template', default=None)
@click.option('--id', default=None)
@click.option('--params', default=None, help='key-value pairs to add to build',
              type=KeyValuePairs())
def build(method, template, id, params):
    print(params)
    if params is None:
        params = {}
    if isinstance(template, str) and template.endswith('.yaml'):
        template = template.split('.yaml')[0]
    _build(template, method, id=id, **params)


if __name__ == '__main__':
    cli()
