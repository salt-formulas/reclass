from reclass import settings
from reclass.values import parser_funcs as pf
import unittest
import ddt


SETTINGS = settings.Settings()

# Test cases for parsers. Each test case is a two-tuple of input string and
# expected output. NOTE: default values for sentinels are used here to avoid
# cluttering up the code.
test_pairs_simple = (
    # Basic test cases.
    ('${foo}', [(pf.tags.REF, [(pf.tags.STR, 'foo')])]),
    # Basic combinations.
    ('bar${foo}', [(pf.tags.STR, 'bar'),
                   (pf.tags.REF, [(pf.tags.STR, 'foo')])]),
    ('bar${foo}baz', [(pf.tags.STR, 'bar'),
                      (pf.tags.REF, [(pf.tags.STR, 'foo')]),
                      (pf.tags.STR, 'baz')]),
    ('${foo}baz', [(pf.tags.REF, [(pf.tags.STR, 'foo')]),
                   (pf.tags.STR, 'baz')]),
    # Whitespace preservation cases.
    ('bar ${foo}', [(pf.tags.STR, 'bar '),
                    (pf.tags.REF, [(pf.tags.STR, 'foo')])]),
    ('bar ${foo baz}', [(pf.tags.STR, 'bar '),
                        (pf.tags.REF, [(pf.tags.STR, 'foo baz')])]),
    ('bar${foo} baz', [(pf.tags.STR, 'bar'),
                       (pf.tags.REF, [(pf.tags.STR, 'foo')]),
                       (pf.tags.STR, ' baz')]),
    (' bar${foo} baz ', [(pf.tags.STR, ' bar'),
                         (pf.tags.REF, [(pf.tags.STR, 'foo')]),
                         (pf.tags.STR, ' baz ')]),
)

# Simple parser test cases are also included in this test grouop.
test_pairs_full = (
    # Single elements sanity.
    ('foo', [(pf.tags.STR, 'foo')]),
    ('$foo', [(pf.tags.STR, '$foo')]),
    ('{foo}', [(pf.tags.STR, '{foo}')]),
    ('[foo]', [(pf.tags.STR, '[foo]')]),
    ('$(foo)', [(pf.tags.STR, '$(foo)')]),
    ('$[foo]', [(pf.tags.INV, [(pf.tags.STR, 'foo')])]),

    # Escape sequences.
    (r'\${foo}', [(pf.tags.STR, '${'), (pf.tags.STR, 'foo}')]),
    # Note the double backslashes '\\' below which python reduces to a
    # single backslash
    (r'\\${foo}', [(pf.tags.STR, '\\'), (pf.tags.REF, [(pf.tags.STR, 'foo')])]),
    # This is probably not would be expected. With \\\\$ the backslash closest to the $ sign
    # is removed and the rest pass through
    #(r'\\\\${foo}', [(pf.tags.STR, r'\\'), (pf.tags.STR, '\\'), (pf.tags.REF, [(pf.tags.STR, 'foo')])]),

    # Basic combinations.
    ('bar$[foo]', [(pf.tags.STR, 'bar'),
                   (pf.tags.INV, [(pf.tags.STR, 'foo')])]),
    ('bar$[foo]baz', [(pf.tags.STR, 'bar'),
                      (pf.tags.INV, [(pf.tags.STR, 'foo')]),
                      (pf.tags.STR, 'baz')]),
    ('$[foo]baz', [(pf.tags.INV, [(pf.tags.STR, 'foo')]),
                   (pf.tags.STR, 'baz')]),

    # Whitespace preservation in various positions.
    (' foo ', [(pf.tags.STR, ' foo ')]),
    ('foo bar', [(pf.tags.STR, 'foo bar')]),
    ('bar $[foo baz]', [(pf.tags.STR, 'bar '),
                        (pf.tags.INV, [(pf.tags.STR, 'foo baz')])]),
    ('bar$[foo] baz ', [(pf.tags.STR, 'bar'),
                        (pf.tags.INV, [(pf.tags.STR, 'foo')]),
                        (pf.tags.STR, ' baz ')]),

    # Nested references and inventory items.
    ('${foo}${bar}',[(pf.tags.REF, [(pf.tags.STR, 'foo')]),
                     (pf.tags.REF, [(pf.tags.STR, 'bar')])]),
    ('${foo${bar}}',[(pf.tags.REF, [(pf.tags.STR, 'foo'),
                                    (pf.tags.REF, [(pf.tags.STR, 'bar')])])]),
    ('$[foo]$[bar]',[(pf.tags.INV, [(pf.tags.STR, 'foo')]),
                     (pf.tags.INV, [(pf.tags.STR, 'bar')])]),
    # NOTE: the cases below do not work as expected, which is probably a bug.
    # Any nesting in INV creates a string.
    #('${$[foo]}', [(pf.tags.REF, [(pf.tags.INV, [(pf.tags.STR, 'foo')])])]),
    #('$[${foo}]', [(pf.tags.INV, [(pf.tags.REF, [(pf.tags.STR, 'foo')])])]),
    #('$[foo$[bar]]',[(pf.tags.INV, [(pf.tags.STR, 'foo'),
    #                                (pf.tags.INV, [(pf.tags.STR, 'bar')])])]),

) + test_pairs_simple


@ddt.ddt
class TestRefParser(unittest.TestCase):

    @ddt.data(*test_pairs_full)
    def test_standard_reference_parser(self, data):
        instring, expected = data
        parser = pf.get_ref_parser(SETTINGS)

        result = pf.listify(parser.parseString(instring).asList())

        self.assertEquals(expected, result)


@ddt.ddt
class TestSimpleRefParser(unittest.TestCase):

    @ddt.data(*test_pairs_simple)
    def test_standard_reference_parser(self, data):
        # NOTE: simple reference parser can parse references only. It fails
        # on inventory items.
        instring, expected = data
        parser = pf.get_simple_ref_parser(SETTINGS)

        result = pf.listify(parser.parseString(instring).asList())

        self.assertEquals(expected, result)


if __name__ == '__main__':
    unittest.main()
