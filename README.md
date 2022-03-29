# sql_to_pypika

[![Tests Status](https://github.com/pahwaranger/sql_to_pypika/workflows/Tests/badge.svg?branch=master&event=push)](https://github.com/pahwaranger/sql_to_pypika/actions/workflows/test.yml?query=event%3Apush+branch%3Amaster) [![codecov](https://codecov.io/gh/pahwaranger/sql_to_pypika/branch/master/graph/badge.svg?token=7T2VXRNGON)](https://codecov.io/gh/pahwaranger/sql_to_pypika) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Helper util for converting raq SQL expressions to PyPika objects. This is neither comprehensive nor perfect. My hope with creating a repo for this is that if people are interested then we can expand on this from here.

## Usage

Testing:

```sh
> poetry run python -m sql_to_pypika.cli eval --tables="[('foo', 'f')]" --sql="fizz=1"
"f"."fizz"=1
```

Usage:

```py
tables = [("foo", "foo"), ("bar", "b")]
evaluator = ExpressionEvaluator(tables)
result = evaluator.eval("foo.fizz = 1")

print(result)  # "foo"."fizz"=1'
type(result)   # pypika.terms.BasicCriterion

result = evaluator.eval("bar.fizz = 1")
print(result)  # "b"."fizz"=1'
type(result)   # pypika.terms.BasicCriterion

```

## Disclaimer

The logic was initially created by @twheys, the creator of PyPika ([gist](https://gist.github.com/twheys/5635a932ca6cfce0d114a86fb55f6c80)) via [this conversation](https://github.com/kayak/pypika/issues/325).

I went ahead and cleaned it up and added some tests so I could use it for my own needs.

## Dev / CI

This repo utilize Poetry, for package management. I recommend reading the Poetry install instructions [here](https://python-poetry.org/docs/#installation).

You can then simply run:

```sh
poetry install
```

We use `pytest` and `Black` for testing and linting respectively. You can use the scripts in the scripts folder to run them.
