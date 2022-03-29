import ast
import click
import pypika

from .evaluator import ExpressionEvaluator


@click.group()
def cli():
    pass


def convert_tables(ctx, param, value):
    if isinstance(value, str):
        value = ast.literal_eval(value)

    if isinstance(value, tuple):
        value = [value]
    elif not isinstance(value, list):
        example = "--tables \"('foo', 'foo')\""
        raise ValueError(f"Table param must be a tuple or list of tuples. Eg: '{example}'")

    return value


@cli.command()
@click.option("--tables", callback=convert_tables, help="Tuple of tables with alias. Eg: ('customers', 'c')")
@click.option("--sql", help="Specify a set of test configs to parse")
def eval(tables, sql):
    evaluator = ExpressionEvaluator(tables=tables)
    result = evaluator.eval(sql)
    print(result)
    return result


if __name__ == "__main__":
    cli(obj={})
