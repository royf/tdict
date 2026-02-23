import operator
import unittest

from tdict import Bunch


class TestBunchInitialization(unittest.TestCase):
    """Test Bunch initialization and construction."""

    def test_empty_initialization(self):
        """Test creating an empty Bunch."""
        b = Bunch()
        self.assertEqual(len(b), 0)

    def test_initialization_with_kwargs(self):
        """Test creating a Bunch with keyword arguments."""
        b = Bunch(a=1, b=2, c=3)
        self.assertEqual(b['a'], 1)
        self.assertEqual(b['b'], 2)
        self.assertEqual(b['c'], 3)

    def test_initialization_with_dict(self):
        """Test creating a Bunch from a dictionary."""
        d = {'x': 10, 'y': 20}
        b = Bunch(d)
        self.assertEqual(b['x'], 10)
        self.assertEqual(b['y'], 20)

    def test_initialization_with_multiple_maps(self):
        """Test creating a Bunch with multiple mappings."""
        map1 = {'a': 1, 'b': 2}
        map2 = {'c': 3, 'd': 4}
        b = Bunch(map1, map2)
        self.assertEqual(len(b), 4)
        self.assertEqual(b['a'], 1)
        self.assertEqual(b['d'], 4)

    def test_initialization_with_maps_and_kwargs(self):
        """Test creating a Bunch with both maps and kwargs."""
        map1 = {'a': 1}
        b = Bunch(map1, b=2, c=3)
        self.assertEqual(b['a'], 1)
        self.assertEqual(b['b'], 2)
        self.assertEqual(b['c'], 3)

    def test_initialization_overlapping_keys(self):
        """Test that later values override earlier ones."""
        map1 = {'a': 1}
        map2 = {'a': 2}
        b = Bunch(map1, map2, a=3)
        self.assertEqual(b['a'], 3)


class TestBunchAttributeAccess(unittest.TestCase):
    """Test attribute-style access to Bunch items."""

    def setUp(self):
        self.b = Bunch(name='John', age=30, city='NYC')

    def test_getattr_access(self):
        """Test accessing items as attributes."""
        self.assertEqual(self.b.name, 'John')
        self.assertEqual(self.b.age, 30)
        self.assertEqual(self.b.city, 'NYC')

    def test_getitem_access(self):
        """Test accessing items via bracket notation."""
        self.assertEqual(self.b['name'], 'John')
        self.assertEqual(self.b['age'], 30)
        self.assertEqual(self.b['city'], 'NYC')

    def test_setattr(self):
        """Test setting items via attribute assignment."""
        self.b.name = 'Jane'
        self.assertEqual(self.b['name'], 'Jane')
        self.assertEqual(self.b.name, 'Jane')

    def test_setitem(self):
        """Test setting items via bracket notation."""
        self.b['age'] = 31
        self.assertEqual(self.b.age, 31)
        self.assertEqual(self.b['age'], 31)

    def test_delattr(self):
        """Test deleting items via attribute deletion."""
        del self.b.name
        self.assertNotIn('name', self.b)
        with self.assertRaises(AttributeError):
            _ = self.b.name

    def test_delitem(self):
        """Test deleting items via bracket notation."""
        del self.b['age']
        self.assertNotIn('age', self.b)
        with self.assertRaises(KeyError):
            _ = self.b['age']

    def test_getattr_nonexistent_raises_attribute_error(self):
        """Test that accessing nonexistent attribute raises AttributeError."""
        with self.assertRaises(AttributeError):
            _ = self.b.nonexistent

    def test_getitem_nonexistent_raises_key_error(self):
        """Test that accessing nonexistent item raises KeyError."""
        with self.assertRaises(KeyError):
            _ = self.b['nonexistent']


class TestBunchStringRepresentations(unittest.TestCase):
    """Test string representations of Bunch."""

    def test_str_representation(self):
        """Test informal string representation."""
        b = Bunch(a=1, b=2)
        s = str(b)
        self.assertIn('Bunch', s)
        self.assertIn('a=1', s)
        self.assertIn('b=2', s)

    def test_repr_representation(self):
        """Test formal string representation."""
        b = Bunch(a=1, b=2)
        r = repr(b)
        self.assertIn('Bunch', r)
        self.assertIn('a=', r)
        self.assertIn('b=', r)

    def test_repr_with_invalid_identifier_keys(self):
        """Test repr with non-identifier keys."""
        b = Bunch(**{'non-identifier': 'value', 'valid_key': 42})
        r = repr(b)
        self.assertIn("'non-identifier'", r)
        self.assertIn('valid_key', r)


class TestBunchMappingProtocol(unittest.TestCase):
    """Test MutableMapping protocol implementation."""

    def setUp(self):
        self.b = Bunch(a=1, b=2, c=3)

    def test_len(self):
        """Test __len__."""
        self.assertEqual(len(self.b), 3)
        self.b['d'] = 4
        self.assertEqual(len(self.b), 4)

    def test_iter(self):
        """Test __iter__."""
        keys = set(self.b)
        self.assertEqual(keys, {'a', 'b', 'c'})

    def test_contains(self):
        """Test __contains__ (in operator)."""
        self.assertIn('a', self.b)
        self.assertNotIn('z', self.b)

    def test_keys(self):
        """Test keys() method."""
        keys = set(self.b.keys())
        self.assertEqual(keys, {'a', 'b', 'c'})

    def test_values(self):
        """Test values() method."""
        values = set(self.b.values())
        self.assertEqual(values, {1, 2, 3})

    def test_items(self):
        """Test items() method."""
        items = set(self.b.items())
        self.assertEqual(items, {('a', 1), ('b', 2), ('c', 3)})


class TestBunchCopy(unittest.TestCase):
    """Test copy functionality."""

    def test_copy_creates_independent_bunch(self):
        """Test that copy creates an independent copy."""
        b1 = Bunch(a=1, b=2)
        b2 = b1.copy()

        # Modify original
        b1['a'] = 999
        b1['new'] = 'value'

        # Copy should be unchanged
        self.assertEqual(b2['a'], 1)
        self.assertNotIn('new', b2)

    def test_copy_shallow_copy_of_values(self):
        """Test that copy is shallow (nested objects are not deep copied)."""
        b1 = Bunch(data=[1, 2, 3])
        b2 = b1.copy()

        # Modifying nested list affects both
        b1['data'].append(4)
        self.assertEqual(b2['data'], [1, 2, 3, 4])


class TestBunchGetItems(unittest.TestCase):
    """Test get_items method."""

    def setUp(self):
        self.b = Bunch(a=1, b=2, c=3)

    def test_get_items_with_iterable(self):
        """Test get_items with an iterable of keys."""
        result = self.b.get_items(['a', 'c'])
        self.assertEqual(len(result), 2)
        self.assertEqual(result['a'], 1)
        self.assertEqual(result['c'], 3)

    def test_get_items_with_missing_keys_iterable(self):
        """Test get_items with missing keys in iterable (omits them)."""
        result = self.b.get_items(['a', 'z', 'c'])
        self.assertEqual(len(result), 2)
        self.assertIn('a', result)
        self.assertIn('c', result)
        self.assertNotIn('z', result)

    def test_get_items_with_mapping(self):
        """Test get_items with a mapping providing defaults."""
        keys_defaults = {'a': 999, 'z': 100, 'b': 888}
        result = self.b.get_items(keys_defaults)
        self.assertEqual(result['a'], 1)  # From bunch
        self.assertEqual(result['z'], 100)  # From defaults
        self.assertEqual(result['b'], 2)  # From bunch

    def test_get_items_empty(self):
        """Test get_items with no keys."""
        result = self.b.get_items([])
        self.assertEqual(len(result), 0)


class TestBunchSetDefaults(unittest.TestCase):
    """Test set_defaults method."""

    def test_set_defaults_new_keys(self):
        """Test setting defaults for new keys."""
        b = Bunch(a=1)
        result = b.set_defaults({'b': 2, 'c': 3})

        # Check result contains only the requested keys
        self.assertEqual(len(result), 2)
        self.assertEqual(result['b'], 2)
        self.assertEqual(result['c'], 3)
        self.assertNotIn('a', result)

        # Check original was modified with the defaults
        self.assertEqual(b['a'], 1)
        self.assertEqual(b['b'], 2)
        self.assertEqual(b['c'], 3)

    def test_set_defaults_existing_keys(self):
        """Test that existing keys are not overwritten."""
        b = Bunch(a=1, b=2)
        result = b.set_defaults({'a': 999, 'c': 3})

        self.assertEqual(result['a'], 1)  # Original value preserved
        self.assertEqual(result['c'], 3)


class TestBunchPopItems(unittest.TestCase):
    """Test pop_items method."""

    def test_pop_items_with_iterable(self):
        """Test pop_items with an iterable."""
        b = Bunch(a=1, b=2, c=3, d=4)
        result = b.pop_items(['a', 'c'])

        # Check result
        self.assertEqual(result['a'], 1)
        self.assertEqual(result['c'], 3)
        self.assertEqual(len(result), 2)

        # Check original was modified
        self.assertEqual(len(b), 2)
        self.assertNotIn('a', b)
        self.assertNotIn('c', b)

    def test_pop_items_with_missing_keys_iterable(self):
        """Test pop_items with missing keys (omits them)."""
        b = Bunch(a=1, b=2)
        result = b.pop_items(['a', 'z'])

        self.assertEqual(len(result), 1)
        self.assertEqual(result['a'], 1)
        self.assertNotIn('z', result)

    def test_pop_items_with_mapping(self):
        """Test pop_items with a mapping providing defaults."""
        b = Bunch(a=1, b=2)
        result = b.pop_items({'a': 999, 'z': 100})

        self.assertEqual(result['a'], 1)
        self.assertEqual(result['z'], 100)
        self.assertNotIn('a', b)
        self.assertEqual(b['b'], 2)

    def test_pop_items_empty_bunch_afterwards(self):
        """Test pop_items removes all items."""
        b = Bunch(x=1, y=2)
        result = b.pop_items(['x', 'y'])

        self.assertEqual(len(b), 0)
        self.assertEqual(len(result), 2)


class TestBunchXorOperator(unittest.TestCase):
    """Test XOR operators for deleting keys."""

    def test_ixor_deletes_keys_inplace(self):
        """Test __ixor__ deletes keys in place."""
        b = Bunch(a=1, b=2, c=3)
        b_id = id(b)
        b ^= ['a', 'c']

        self.assertEqual(len(b), 1)
        self.assertEqual(b['b'], 2)
        self.assertEqual(id(b), b_id)  # Same object

    def test_xor_returns_copy_with_keys_deleted(self):
        """Test __xor__ returns new Bunch with keys deleted."""
        b = Bunch(a=1, b=2, c=3)
        result = b ^ ['a', 'c']

        # Original should be unchanged
        self.assertEqual(len(b), 3)
        self.assertIn('a', b)
        self.assertIn('c', b)

        # Result should have keys deleted
        self.assertEqual(len(result), 1)
        self.assertEqual(result['b'], 2)
        self.assertNotIn('a', result)
        self.assertNotIn('c', result)


class TestBunchMerge(unittest.TestCase):
    """Test merge functionality."""

    def test_merge_with_add_operator(self):
        """Test merge with addition operator."""
        b = Bunch(a=1, b=2)
        b.merge({'a': 10, 'c': 3}, operator.add)

        self.assertEqual(b['a'], 11)  # 1 + 10
        self.assertEqual(b['b'], 2)
        self.assertEqual(b['c'], 3)

    def test_merge_with_multiply_operator(self):
        """Test merge with multiplication operator."""
        b = Bunch(a=5, b=2)
        b.merge({'a': 3, 'c': 2}, operator.mul)

        self.assertEqual(b['a'], 15)  # 5 * 3
        self.assertEqual(b['b'], 2)
        self.assertEqual(b['c'], 2)

    def test_merge_new_keys_added(self):
        """Test that new keys are simply added."""
        b = Bunch(a=1)
        b.merge({'b': 2, 'c': 3}, operator.add)

        self.assertEqual(b['b'], 2)
        self.assertEqual(b['c'], 3)

    def test_merge_with_custom_operator(self):
        """Test merge with custom operator."""
        b = Bunch(a=10, b=20)
        b.merge({'a': 3, 'c': 5}, lambda x, y: x - y)

        self.assertEqual(b['a'], 7)  # 10 - 3


class TestBunchArithmeticOperators(unittest.TestCase):
    """Test arithmetic operators on Bunch."""

    def test_add_operator(self):
        """Test addition operator."""
        b1 = Bunch(a=1, b=2)
        b2 = Bunch(a=10, c=3)

        result = b1 + b2

        self.assertEqual(result['a'], 11)
        self.assertEqual(result['b'], 2)
        self.assertEqual(result['c'], 3)
        # Original unchanged
        self.assertEqual(b1['a'], 1)

    def test_iadd_operator_inplace(self):
        """Test in-place addition operator."""
        b1 = Bunch(a=1, b=2)
        b2 = Bunch(a=10, c=3)

        b1_id = id(b1)
        b1 += b2

        self.assertEqual(b1['a'], 11)
        self.assertEqual(b1['c'], 3)
        self.assertEqual(id(b1), b1_id)  # Same object

    def test_sub_operator(self):
        """Test subtraction operator."""
        b1 = Bunch(a=10, b=5)
        b2 = Bunch(a=3, c=2)

        result = b1 - b2

        self.assertEqual(result['a'], 7)
        self.assertEqual(result['b'], 5)
        self.assertEqual(result['c'], 2)

    def test_mul_operator(self):
        """Test multiplication operator."""
        b1 = Bunch(a=2, b=3)
        b2 = Bunch(a=5, c=4)

        result = b1 * b2

        self.assertEqual(result['a'], 10)
        self.assertEqual(result['b'], 3)
        self.assertEqual(result['c'], 4)

    def test_truediv_operator(self):
        """Test true division operator."""
        b1 = Bunch(a=10, b=5)
        b2 = Bunch(a=2, c=2)

        result = b1 / b2

        self.assertEqual(result['a'], 5.0)
        self.assertEqual(result['b'], 5)
        self.assertEqual(result['c'], 2)

    def test_floordiv_operator(self):
        """Test floor division operator."""
        b1 = Bunch(a=10, b=5)
        b2 = Bunch(a=3, c=2)

        result = b1 // b2

        self.assertEqual(result['a'], 3)
        self.assertEqual(result['b'], 5)
        self.assertEqual(result['c'], 2)

    def test_mod_operator(self):
        """Test modulo operator."""
        b1 = Bunch(a=10, b=5)
        b2 = Bunch(a=3, c=2)

        result = b1 % b2

        self.assertEqual(result['a'], 1)
        self.assertEqual(result['b'], 5)
        self.assertEqual(result['c'], 2)

    def test_pow_operator(self):
        """Test power operator."""
        b1 = Bunch(a=2, b=3)
        b2 = Bunch(a=3, c=2)

        result = b1 ** b2

        self.assertEqual(result['a'], 8)  # 2 ** 3
        self.assertEqual(result['b'], 3)
        self.assertEqual(result['c'], 2)

    def test_or_operator(self):
        """Test OR operator (replaces value with other value)."""
        b1 = Bunch(a=1, b=2)
        b2 = Bunch(a=10, c=3)

        result = b1 | b2

        self.assertEqual(result['a'], 10)  # Takes value from b2
        self.assertEqual(result['b'], 2)
        self.assertEqual(result['c'], 3)

    def test_lshift_operator(self):
        """Test left shift operator."""
        b1 = Bunch(a=2, b=1)
        b2 = Bunch(a=3, c=1)

        result = b1 << b2

        self.assertEqual(result['a'], 16)  # 2 << 3
        self.assertEqual(result['b'], 1)
        self.assertEqual(result['c'], 1)

    def test_rshift_operator(self):
        """Test right shift operator."""
        b1 = Bunch(a=16, b=2)
        b2 = Bunch(a=2, c=1)

        result = b1 >> b2

        self.assertEqual(result['a'], 4)  # 16 >> 2
        self.assertEqual(result['b'], 2)
        self.assertEqual(result['c'], 1)


class MatmulType:
    """Custom type that supports matmul operator."""

    def __init__(self, value):
        self.value = value

    def __matmul__(self, other):
        """Matmul returns combined value."""
        return MatmulType(self.value + other.value)

    def __eq__(self, other):
        return isinstance(other, MatmulType) and self.value == other.value

    def __repr__(self):
        return f'MatmulType({self.value})'


class TestBunchMatmulOperator(unittest.TestCase):
    """Test matrix multiplication operator."""

    def test_matmul_operator(self):
        """Test @ operator (matrix multiplication)."""
        b1 = Bunch(a=MatmulType(2), b=MatmulType(3))
        b2 = Bunch(a=MatmulType(4), c=MatmulType(5))

        result = b1 @ b2

        self.assertEqual(result['a'], MatmulType(6))  # 2 @ 4 = 2 + 4
        self.assertEqual(result['b'], MatmulType(3))
        self.assertEqual(result['c'], MatmulType(5))


class TestBunchEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""

    def test_empty_bunch_operations(self):
        """Test operations on empty Bunch."""
        b = Bunch()
        self.assertEqual(len(b), 0)
        self.assertEqual(list(b), [])
        self.assertEqual(repr(b), 'Bunch()')

    def test_bunch_with_none_values(self):
        """Test Bunch with None values."""
        b = Bunch(a=None, b=2)
        self.assertIsNone(b['a'])
        self.assertEqual(b['b'], 2)

    def test_bunch_with_numeric_string_keys(self):
        """Test Bunch with numeric string keys."""
        b = Bunch(**{'123': 'value', 'abc': 'other'})
        self.assertEqual(b['123'], 'value')
        self.assertEqual(b['abc'], 'other')

    def test_bunch_nested(self):
        """Test nested Bunch objects."""
        inner = Bunch(x=1, y=2)
        outer = Bunch(inner=inner, z=3)

        self.assertEqual(outer['inner']['x'], 1)
        self.assertEqual(outer.inner.x, 1)

    def test_large_bunch(self):
        """Test Bunch with many items."""
        data = {f'key_{i}': i for i in range(1000)}
        b = Bunch(data)

        self.assertEqual(len(b), 1000)
        self.assertEqual(b['key_500'], 500)

    def test_bunch_from_bunch(self):
        """Test creating Bunch from another Bunch."""
        b1 = Bunch(a=1, b=2)
        b2 = Bunch(b1, c=3)

        self.assertEqual(b2['a'], 1)
        self.assertEqual(b2['b'], 2)
        self.assertEqual(b2['c'], 3)

    def test_special_characters_in_keys(self):
        """Test Bunch with special characters in keys."""
        b = Bunch(**{'a-b': 1, 'a.b': 2, 'a b': 3})
        self.assertEqual(b['a-b'], 1)
        self.assertEqual(b['a.b'], 2)
        self.assertEqual(b['a b'], 3)

    def test_update_method_inherited_from_mapping(self):
        """Test inherited update method."""
        b = Bunch(a=1)
        b.update({'b': 2, 'c': 3})

        self.assertEqual(b['a'], 1)
        self.assertEqual(b['b'], 2)
        self.assertEqual(b['c'], 3)

    def test_get_method_inherited_from_mapping(self):
        """Test inherited get method with defaults."""
        b = Bunch(a=1)
        self.assertEqual(b.get('a'), 1)
        self.assertIsNone(b.get('b'))
        self.assertEqual(b.get('b', 999), 999)


class TestBunchTypeCheck(unittest.TestCase):
    """Test type checking and instance validation."""

    def test_bunch_is_mutable_mapping(self):
        """Test that Bunch is a MutableMapping."""
        b = Bunch(a=1)
        from collections.abc import MutableMapping
        self.assertIsInstance(b, MutableMapping)

    def test_bunch_isinstance_mapping(self):
        """Test that Bunch is a Mapping."""
        b = Bunch(a=1)
        from collections.abc import Mapping
        self.assertIsInstance(b, Mapping)


if __name__ == '__main__':
    unittest.main()
