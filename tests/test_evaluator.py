import pytest
from pypika import terms, functions, enums
from sql_to_pypika.evaluator import ExpressionEvaluator
from sql_to_pypika.exceptions import ExpressionSyntaxError

tables = [("foo", "foo"), ("bar", "b")]
evaluator = ExpressionEvaluator(tables)

single_table = [("foo", "f")]
single_table_evaluator = ExpressionEvaluator(single_table)


class TestExpressions:
    def _compare(self, inst, expression, expected):
        result = evaluator.eval(expression)
        assert str(result) == expected
        assert isinstance(result, inst)

    def _compare_single(self, inst, expression, expected):
        """some logic works differently when we only provide a single table to generate expression from"""
        result = single_table_evaluator.eval(expression)
        assert str(result) == expected
        assert isinstance(result, inst)

    def _raise(self, expression, exception_type=Exception):
        with pytest.raises(exception_type):
            evaluator.eval(expression)

    def test_expressions(self):
        # improper aliasing
        self._raise("b.fizz")
        self._raise("fizz")
        self._raise("desc", exception_type=ExpressionSyntaxError)
        self._raise("", exception_type=ExpressionSyntaxError)

        # works if only one table exists
        self._compare_single(terms.Field, "fizz", '"f"."fizz"')

        # simple field
        self._compare(terms.Field, "foo.fizz", '"foo"."fizz"')
        self._compare(terms.Field, 'foo."fizz"', '"foo"."fizz"')  # quoted field
        self._compare(terms.Field, "foo.fizz\n", '"foo"."fizz"')  # trim newlines
        self._compare(terms.Field, "foo.fizz\n ", '"foo"."fizz"')  # trim newlines
        self._compare(terms.ValueWrapper, "1", "1")
        self._compare(terms.ValueWrapper, "1.0", "1.0")
        self._compare(terms.Bracket, "(foo.fizz)", '("foo"."fizz")')
        self._compare(terms.Not, "NOT foo.fizz", 'NOT "foo"."fizz"')
        # -> uppers
        for term, term_type in [("null", terms.NullValue)]:
            self._compare(term_type, term.lower(), term.upper())
            self._compare(term_type, term.upper(), term.upper())
            self._compare(term_type, term.title(), term.upper())
        # -> lowers
        for term, term_type in [("true", terms.ValueWrapper), ("false", terms.ValueWrapper)]:
            self._compare(term_type, term.lower(), term.lower())
            self._compare(term_type, term.upper(), term.lower())
            self._compare(term_type, term.title(), term.lower())

        # concat
        self._compare(functions.Concat, "foo.fizz || foo.fizz", 'CONCAT("foo"."fizz","foo"."fizz")')
        self._compare(
            functions.Concat, "foo.fizz || foo.fizz || foo.fizz", 'CONCAT("foo"."fizz","foo"."fizz","foo"."fizz")'
        )

        # generate query with alias if alias exists
        self._compare(terms.BasicCriterion, "foo.fizz = 1", '"foo"."fizz"=1')
        self._compare(terms.BasicCriterion, "bar.fizz = 1", '"b"."fizz"=1')

    def test_equalities(self):
        self._compare(terms.BasicCriterion, "bar.fizz != 1", '"b"."fizz"<>1')
        for op in ["=", "<>", "<=", "<", ">=", ">"]:
            self._compare(terms.BasicCriterion, f"bar.fizz {op} 1", f'"b"."fizz"{op}1')

        for op in ["LIKE", "NOT LIKE", "ILIKE", "NOT ILIKE"]:
            self._compare(terms.BasicCriterion, f"bar.fizz {op} '1%'", f'"b"."fizz" {op} \'1%\'')

        self._compare(terms.NullCriterion, "bar.fizz IS NULL", '"b"."fizz" IS NULL')
        self._compare(terms.Not, "bar.fizz IS NOT NULL", 'NOT "b"."fizz" IS NULL')

        # contains
        for op in ["IN", "NOT IN"]:
            self._compare(terms.ContainsCriterion, f"bar.fizz {op} (1, 2)", f'"b"."fizz" {op} (1,2)')

        # combinations
        self._compare(terms.BetweenCriterion, "foo.fizz BETWEEN 1 AND 2", '"foo"."fizz" BETWEEN 1 AND 2')
        self._compare(terms.ComplexCriterion, "foo.fizz = 1 OR foo.fizz = 2", '"foo"."fizz"=1 OR "foo"."fizz"=2')
        self._compare(terms.ComplexCriterion, "foo.fizz >= 1 AND foo.fizz <= 2", '"foo"."fizz">=1 AND "foo"."fizz"<=2')
        self._compare(terms.Bracket, "(foo.fizz = 1 OR foo.fizz = 2)", '("foo"."fizz"=1 OR "foo"."fizz"=2)')

    def test_arithmetic(self):
        self._compare(terms.Mod, "bar.fizz % 1", 'MOD("b"."fizz",1)')
        for op in ["+", "-", "*", "/"]:
            self._compare(terms.ArithmeticExpression, f"bar.fizz {op} 1", f'"b"."fizz"{op}1')

    def test_statements(self):
        # case statement
        self._compare(
            terms.Case, "CASE foo.fizz WHEN 1 THEN 1 ELSE 0 END", "CASE WHEN 1 THEN 1 ELSE 0 END"
        )  # TODO: fix
        self._compare(
            terms.Case, "CASE foo.fizz WHEN 1 THEN 1 WHEN 2 THEN 2 END", "CASE WHEN 1 THEN 1 WHEN 2 THEN 2 END"
        )  # TODO: fix
        self._compare(
            terms.Case, "CASE WHEN foo.fizz = 1 THEN 1 ELSE 0 END", 'CASE WHEN "foo"."fizz"=1 THEN 1 ELSE 0 END'
        )
        self._compare(
            terms.Case,
            "CASE WHEN foo.fizz = 1 THEN 1 WHEN foo.fizz = 2 THEN 2 END",
            'CASE WHEN "foo"."fizz"=1 THEN 1 WHEN "foo"."fizz"=2 THEN 2 END',
        )

        # aggregates
        self._compare(terms.AggregateFunction, "SUM(foo.fizz)", 'SUM("foo"."fizz")')

    def test_analytical_functions(self):
        self._compare(
            terms.AggregateFunction,
            "SUM(foo.fizz) OVER(partition by bar.buzz)",
            'SUM("foo"."fizz") OVER(PARTITION BY "b"."buzz")',
        )
        self._compare(
            terms.AggregateFunction,
            "SUM(foo.fizz IGNORE NULLS) OVER(partition by bar.buzz)",
            'SUM("foo"."fizz" IGNORE NULLS) OVER(PARTITION BY "b"."buzz")',
        )
        self._compare(
            terms.AggregateFunction,
            "SUM(foo.fizz) OVER(order by bar.buzz)",
            'SUM("foo"."fizz") OVER(ORDER BY "b"."buzz")',
        )
        self._compare(
            terms.AggregateFunction,
            "SUM(foo.fizz) OVER(order by bar.buzz asc)",
            'SUM("foo"."fizz") OVER(ORDER BY "b"."buzz" ASC)',
        )
        self._compare(
            terms.AggregateFunction,
            "SUM(foo.fizz) OVER(order by bar.buzz desc)",
            'SUM("foo"."fizz") OVER(ORDER BY "b"."buzz" DESC)',
        )
        self._compare(
            terms.AggregateFunction,
            "SUM(foo.fizz) OVER(order by bar.buzz, bar.bizz desc)",
            'SUM("foo"."fizz") OVER(ORDER BY "b"."buzz","b"."bizz" DESC)',
        )
        self._compare(
            terms.AggregateFunction,
            "SUM(foo.fizz) OVER(order by bar.buzz, bar.bizz)",
            'SUM("foo"."fizz") OVER(ORDER BY "b"."buzz","b"."bizz")',
        )
        self._compare(
            terms.AggregateFunction,
            "SUM(foo.fizz) OVER(partition by bar.buzz order by bar.buzz)",
            'SUM("foo"."fizz") OVER(PARTITION BY "b"."buzz" ORDER BY "b"."buzz")',
        )

    def test_data_types(self):
        sql_types = [
            "INTEGER",
            "FLOAT",
            "NUMERIC",
            "SIGNED",
            "UNSIGNED",
            "BOOLEAN",
        ]
        sql_types_with_args = [
            "CHAR",
            "VARCHAR",
            "BINARY",
            "VARBINARY",
        ]
        for sql_type in sql_types + sql_types_with_args:
            self._compare(
                functions.Cast,
                f"CAST(foo.fizz AS {sql_type})",
                f'CAST("foo"."fizz" AS {sql_type})',
            )

        for sql_type in sql_types_with_args:
            self._compare(
                functions.Cast,
                f"CAST(foo.fizz AS {sql_type}(1))",
                f'CAST("foo"."fizz" AS {sql_type}(1))',
            )

        self._compare(
            functions.Cast,
            f"CAST(foo.fizz AS LONG VARCHAR)",
            f'CAST("foo"."fizz" AS LONG VARCHAR)',
        )

        self._compare(
            functions.Cast,
            f"CAST(foo.fizz AS LONG VARBINARY)",
            f'CAST("foo"."fizz" AS LONG VARBINARY)',
        )

    def test_times(self):
        times = ["YEAR", "QUARTER", "MONTH", "WEEK", "DAY", "HOUR", "MINUTE", "SECOND", "MICROSECOND"]
        for time in times:
            self._compare(
                enums.DatePart,
                f"{time}",
                f"DatePart.{time.lower()}",
            )
