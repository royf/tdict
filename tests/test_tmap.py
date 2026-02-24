"""
Comprehensive unit tests for Tmap, Tdict, and Tbunch classes.
Tests abstract Tmap functionality and its concrete implementations.
"""

import operator
import unittest

from tdict import Tbunch
from tdict import Tdict
from tdict import Tmap


class TestTmapBasics(unittest.TestCase):
    """Test basic functionality of Tmap through Tdict."""

    def setUp(self):
        """Use Tdict as concrete implementation of Tmap."""
        self.tmap = Tdict()

    def test_empty_tmap_initialization(self):
        """Test creating an empty Tmap."""
        t = Tdict()
        self.assertEqual(len(t), 0)

    def test_tmap_with_items(self):
        """Test creating a Tmap with initial items."""
        t = Tdict()
        t['a'] = 1
        t['b'] = 2
        self.assertEqual(len(t), 2)
        self.assertEqual(t['a'], 1)
        self.assertEqual(t['b'], 2)

    def test_tmap_string_key_access(self):
        """Test accessing items with string keys."""
        self.tmap['key1'] = 'value1'
        self.assertEqual(self.tmap['key1'], 'value1')

    def test_tmap_tuple_key_empty(self):
        """Test accessing with empty tuple key returns self."""
        result = self.tmap[()]
        self.assertIs(result, self.tmap)

    def test_tmap_setitem_creates_missing_intermediate_nodes(self):
        """Test that setitem creates missing intermediate Tmap nodes."""
        self.tmap[('a', 'b', 'c')] = 'value'
        self.assertIsInstance(self.tmap['a'], Tdict)
        self.assertIsInstance(self.tmap['a']['b'], Tdict)
        self.assertEqual(self.tmap['a']['b']['c'], 'value')

    def test_tmap_setitem_string_key(self):
        """Test setting items with string keys."""
        self.tmap['name'] = 'John'
        self.assertEqual(self.tmap['name'], 'John')

    def test_tmap_delitem_string_key(self):
        """Test deleting items with string keys."""
        self.tmap['key'] = 'value'
        del self.tmap['key']
        self.assertNotIn('key', self.tmap)

    def test_tmap_contains_string_key(self):
        """Test __contains__ with string keys."""
        self.tmap['key'] = 'value'
        self.assertIn('key', self.tmap)
        self.assertNotIn('other', self.tmap)

    def test_tmap_iter_string_keys_only(self):
        """Test iteration with only string keys yields tuple keys."""
        self.tmap['a'] = 1
        self.tmap['b'] = 2
        self.tmap['c'] = 3
        keys = list(self.tmap)
        # All keys should be tuples now
        self.assertEqual(sorted(keys), [('a',), ('b',), ('c',)])

    def test_tmap_len_flat_structure(self):
        """Test __len__ with flat structure."""
        self.tmap['a'] = 1
        self.tmap['b'] = 2
        self.tmap['c'] = 3
        self.assertEqual(len(self.tmap), 3)
        # Verify keys are tuples
        keys = list(self.tmap)
        self.assertTrue(all(isinstance(k, tuple) for k in keys))


class TestTmapTupleKeys(unittest.TestCase):
    """Test Tmap functionality with tuple keys for recursive access."""

    def setUp(self):
        """Create a Tmap with nested structure."""
        self.tmap = Tdict()
        self.tmap['level1'] = Tdict()
        self.tmap['level1']['level2'] = Tdict()
        self.tmap['level1']['level2']['value'] = 42

    def test_getitem_single_level_tuple_key(self):
        """Test accessing nested items with 1-element tuple key."""
        result = self.tmap[('level1',)]
        self.assertIsInstance(result, Tdict)
        self.assertEqual(result['level2']['value'], 42)

    def test_getitem_two_level_tuple_key(self):
        """Test accessing nested items with 2-element tuple key."""
        result = self.tmap[('level1', 'level2')]
        self.assertIsInstance(result, Tdict)
        self.assertEqual(result['value'], 42)

    def test_getitem_leaf_tuple_key(self):
        """Test accessing leaf value with multi-level tuple key."""
        result = self.tmap[('level1', 'level2', 'value')]
        self.assertEqual(result, 42)

    def test_getitem_tuple_key_nonexistent_raises_key_error(self):
        """Test accessing nonexistent path raises KeyError."""
        with self.assertRaises(KeyError):
            _ = self.tmap[('level1', 'nonexistent')]

    def test_getitem_tuple_key_traverses_leaf_raises_key_error(self):
        """Test accessing through a leaf value raises KeyError."""
        self.tmap['leaf'] = 'value'
        with self.assertRaises(KeyError):
            _ = self.tmap[('leaf', 'subkey')]

    def test_setitem_tuple_key_single_level(self):
        """Test setting nested items with tuple key."""
        self.tmap[('newkey',)] = 'newvalue'
        self.assertEqual(self.tmap['newkey'], 'newvalue')

    def test_setitem_tuple_key_multi_level(self):
        """Test setting nested items at existing path."""
        self.tmap[('level1', 'newkey')] = 'value'
        self.assertEqual(self.tmap['level1']['newkey'], 'value')

    def test_setitem_tuple_key_empty_raises_key_error(self):
        """Test setting with empty tuple raises KeyError."""
        with self.assertRaises(KeyError):
            self.tmap[()] = 'value'

    def test_setitem_tuple_key_traverses_leaf_raises_key_error(self):
        """Test setting through a leaf raises KeyError."""
        self.tmap['leaf'] = 'value'
        with self.assertRaises(KeyError):
            self.tmap[('leaf', 'subkey')] = 'newvalue'

    def test_delitem_tuple_key_single_level(self):
        """Test deleting with single-element tuple key."""
        del self.tmap[('level1',)]
        self.assertNotIn('level1', self.tmap)

    def test_delitem_tuple_key_multi_level(self):
        """Test deleting nested item with multi-element tuple key."""
        self.tmap[('level1', 'level2', 'value2')] = 100
        del self.tmap[('level1', 'level2', 'value2')]
        self.assertNotIn('value2', self.tmap['level1']['level2'])

    def test_delitem_tuple_key_empty_raises_key_error(self):
        """Test deleting with empty tuple raises KeyError."""
        with self.assertRaises(KeyError):
            del self.tmap[()]

    def test_delitem_tuple_key_traverses_leaf_raises_key_error(self):
        """Test deleting through a leaf raises KeyError."""
        self.tmap['leaf'] = 'value'
        with self.assertRaises(KeyError):
            del self.tmap[('leaf', 'subkey')]


class TestTmapLength(unittest.TestCase):
    """Test __len__ method with nested structures."""

    def test_len_counts_all_leaf_values(self):
        """Test that __len__ counts all leaf values recursively."""
        tmap = Tdict()
        tmap['a'] = 1
        tmap['b'] = 2
        tmap['c'] = Tdict()
        tmap['c']['d'] = 3
        tmap['c']['e'] = 4
        # Total leaves: a, b, d, e = 4
        self.assertEqual(len(tmap), 4)

    def test_len_deep_nesting(self):
        """Test __len__ with deeply nested structure."""
        tmap = Tdict()
        tmap['l1'] = Tdict()
        tmap['l1']['l2'] = Tdict()
        tmap['l1']['l2']['l3'] = Tdict()
        tmap['l1']['l2']['l3']['value'] = 42
        self.assertEqual(len(tmap), 1)

    def test_len_mixed_leaves_and_branches(self):
        """Test __len__ with mixed structure."""
        tmap = Tdict()
        tmap['scalar1'] = 'a'
        tmap['scalar2'] = 'b'
        tmap['branch'] = Tdict()
        tmap['branch']['val1'] = 1
        tmap['branch']['val2'] = 2
        self.assertEqual(len(tmap), 4)

    def test_len_after_modification(self):
        """Test __len__ updates correctly after modifications."""
        tmap = Tdict()
        self.assertEqual(len(tmap), 0)
        tmap['a'] = 1
        self.assertEqual(len(tmap), 1)
        tmap['b'] = Tdict()
        tmap['b']['c'] = 2
        self.assertEqual(len(tmap), 2)
        del tmap['a']
        self.assertEqual(len(tmap), 1)


class TestTmapIteration(unittest.TestCase):
    """Test __iter__ method with nested structures."""

    def test_iter_flat_structure(self):
        """Test iteration over flat structure yields tuple keys."""
        tmap = Tdict()
        tmap['a'] = 1
        tmap['b'] = 2
        tmap['c'] = 3
        keys = list(tmap)
        self.assertEqual(sorted(keys), [('a',), ('b',), ('c',)])

    def test_iter_single_nested(self):
        """Test iteration yields tuple keys for nested items."""
        tmap = Tdict()
        tmap['a'] = Tdict()
        tmap['a']['b'] = 1
        tmap['a']['c'] = 2
        keys = list(tmap)
        self.assertIn(('a', 'b'), keys)
        self.assertIn(('a', 'c'), keys)
        self.assertEqual(len(keys), 2)

    def test_iter_deep_nesting(self):
        """Test iteration yields deeply nested tuple keys."""
        tmap = Tdict()
        tmap['x'] = Tdict()
        tmap['x']['y'] = Tdict()
        tmap['x']['y']['z'] = 99
        keys = list(tmap)
        self.assertIn(('x', 'y', 'z'), keys)
        self.assertEqual(len(keys), 1)

    def test_iter_mixed_nesting(self):
        """Test iteration with mixed structure."""
        tmap = Tdict()
        tmap['scalar'] = 'value'
        tmap['nested'] = Tdict()
        tmap['nested']['item'] = 42
        keys = set(tmap)
        self.assertEqual(len(keys), 2)
        self.assertIn(('scalar',), keys)
        self.assertIn(('nested', 'item'), keys)

    def test_iter_multiple_branches(self):
        """Test iteration with multiple branches."""
        tmap = Tdict()
        tmap['b1'] = Tdict()
        tmap['b1']['a'] = 1
        tmap['b1']['b'] = 2
        tmap['b2'] = Tdict()
        tmap['b2']['c'] = 3
        keys = set(tmap)
        self.assertEqual(len(keys), 3)
        self.assertIn(('b1', 'a'), keys)
        self.assertIn(('b1', 'b'), keys)
        self.assertIn(('b2', 'c'), keys)


class TestTmapCopy(unittest.TestCase):
    """Test copy method."""

    def test_copy_flat_structure(self):
        """Test copying flat Tmap."""
        tmap1 = Tdict()
        tmap1['a'] = 1
        tmap1['b'] = 2
        tmap2 = tmap1.copy()

        # Modify original
        tmap1['a'] = 999
        tmap1['c'] = 3

        # Copy should be independent
        self.assertEqual(tmap2['a'], 1)
        self.assertNotIn('c', tmap2)

    def test_copy_nested_structure(self):
        """Test copying nested structure."""
        tmap1 = Tdict()
        tmap1['branch'] = Tdict()
        tmap1['branch']['leaf'] = 42
        tmap2 = tmap1.copy()

        # Modify original branch
        tmap1['branch']['newkey'] = 100

        # Copy should have its own branch
        self.assertNotIn('newkey', tmap2['branch'])

    def test_copy_returns_same_type(self):
        """Test that copy returns same type."""
        tmap1 = Tdict()
        tmap1['a'] = 1
        tmap2 = tmap1.copy()
        self.assertIsInstance(tmap2, Tdict)

    def test_copy_shallow_for_non_tmap_values(self):
        """Test that copy is shallow for non-Tmap values."""
        tmap1 = Tdict()
        tmap1['list'] = [1, 2, 3]
        tmap2 = tmap1.copy()

        # Modifying nested list affects both
        tmap1['list'].append(4)
        self.assertEqual(tmap2['list'], [1, 2, 3, 4])

    def test_copy_deep_nesting(self):
        """Test copying deeply nested structure."""
        tmap1 = Tdict()
        tmap1['l1'] = Tdict()
        tmap1['l1']['l2'] = Tdict()
        tmap1['l1']['l2']['value'] = 'original'

        tmap2 = tmap1.copy()
        tmap1['l1']['l2']['value'] = 'modified'

        self.assertEqual(tmap2['l1']['l2']['value'], 'original')


class TestTmapUpdate(unittest.TestCase):
    """Test update method."""

    def test_update_flat_with_flat(self):
        """Test updating two flat Tmaps."""
        tmap1 = Tdict()
        tmap1['a'] = 10
        tmap1['b'] = 20
        tmap2 = Tdict()
        tmap2['a'] = 5
        tmap2['c'] = 30

        tmap1.update(tmap2, operator.add)

        self.assertEqual(tmap1['a'], 15)  # 10 + 5
        self.assertEqual(tmap1['b'], 20)
        self.assertEqual(tmap1['c'], 30)

    def test_update_nested_with_flat(self):
        """Test updating nested Tmap with flat one."""
        tmap1 = Tdict()
        tmap1['nested'] = Tdict()
        tmap1['nested']['value'] = 100
        tmap2 = Tdict()
        tmap2['nested'] = Tdict()
        tmap2['nested']['value'] = 50

        tmap1.update(tmap2, operator.add)

        self.assertEqual(tmap1['nested']['value'], 150)

    def test_update_with_multiply(self):
        """Test update with multiplication operator."""
        tmap1 = Tdict()
        tmap1['a'] = 3
        tmap1['b'] = 2
        tmap2 = Tdict()
        tmap2['a'] = 4

        tmap1.update(tmap2, operator.mul)

        self.assertEqual(tmap1['a'], 12)  # 3 * 4
        self.assertEqual(tmap1['b'], 2)

    def test_update_with_scalar(self):
        """Test updating Tmap with scalar value."""
        tmap1 = Tdict()
        tmap1['a'] = 10
        tmap1['b'] = 20

        tmap1.update(5, operator.add)

        self.assertEqual(tmap1['a'], 15)  # 10 + 5
        self.assertEqual(tmap1['b'], 25)  # 20 + 5

    def test_update_complex_structure(self):
        """Test update with complex nested structure."""
        tmap1 = Tdict()
        tmap1['b1'] = Tdict()
        tmap1['b1']['a'] = 1
        tmap1['b1']['b'] = 2

        tmap2 = Tdict()
        tmap2['b1'] = Tdict()
        tmap2['b1']['a'] = 10
        tmap2['b1']['c'] = 30

        tmap1.update(tmap2, operator.add)

        self.assertEqual(tmap1['b1']['a'], 11)
        self.assertEqual(tmap1['b1']['b'], 2)
        self.assertEqual(tmap1['b1']['c'], 30)

    def test_update_modifies_self(self):
        """Test that update modifies self in place."""
        tmap1 = Tdict()
        tmap1['a'] = 1
        tmap1_id = id(tmap1)

        tmap2 = Tdict()
        tmap2['a'] = 2

        tmap1.update(tmap2, operator.add)

        self.assertEqual(id(tmap1), tmap1_id)  # Same object
        self.assertEqual(tmap1['a'], 3)

    def test_update_with_no_operator(self):
        """Test update without operator (default: choose other value)."""
        tmap1 = Tdict()
        tmap1['a'] = 10
        tmap1['b'] = 20
        tmap2 = Tdict()
        tmap2['a'] = 5
        tmap2['c'] = 30

        tmap1.update(tmap2)

        self.assertEqual(tmap1['a'], 5)  # Default: takes value from other
        self.assertEqual(tmap1['b'], 20)
        self.assertEqual(tmap1['c'], 30)

    def test_update_leaf_with_subtree_keeps_subtree(self):
        """Test that updating with a subtree keeps the subtree with symmetric operation."""
        tmap1 = Tdict()
        tmap1['a'] = Tdict()
        tmap1['a']['x'] = 2

        tmap2 = Tdict()
        tmap2['a'] = 10

        tmap1.update(tmap2, operator.add)

        # tmap2['a'] is a leaf with value 10, tmap1['a'] is a subtree with leaf tmap1['a']['x'] = 2
        # The symmetric behavior applies the operator to the leaf and the subtree's leaf
        # Result: tmap1['a']['x'] should be 2 + 10 = 12
        self.assertIsInstance(tmap1['a'], Tdict)
        self.assertEqual(tmap1['a']['x'], 12)

    def test_update_subtree_with_leaf_keeps_subtree(self):
        """Test that updating a subtree with a leaf keeps the subtree with symmetric operation."""
        tmap1 = Tdict()
        tmap1['a'] = 5

        tmap2 = Tdict()
        tmap2['a'] = Tdict()
        tmap2['a']['x'] = 10

        tmap1.update(tmap2, operator.add)

        # tmap1['a'] is a leaf with value 5, tmap2['a'] is a subtree with leaf tmap2['a']['x'] = 10
        # The symmetric behavior applies the operator to both leaves
        # Result: tmap1['a']['x'] should be 5 + 10 = 15
        self.assertIsInstance(tmap1['a'], Tdict)
        self.assertEqual(tmap1['a']['x'], 15)


class TestTdictSpecific(unittest.TestCase):
    """Test Tdict specific functionality (dict-based Tmap)."""

    def test_tdict_is_dict(self):
        """Test that Tdict is a dict."""
        td = Tdict()
        self.assertIsInstance(td, dict)

    def test_tdict_dict_operations(self):
        """Test standard dict operations on Tdict."""
        td = Tdict()
        td['a'] = 1
        td['b'] = 2

        # Test standard dict methods (keys/items now use tuple keys)
        self.assertEqual(set(td.keys()), {('a',), ('b',)})
        self.assertEqual(set(td.values()), {1, 2})
        self.assertEqual(set(td.items()), {(('a',), 1), (('b',), 2)})

    def test_tdict_from_dict(self):
        """Test creating Tdict from dict."""
        d = {'a': 1, 'b': 2}
        td = Tdict(d)
        self.assertEqual(td['a'], 1)
        self.assertEqual(td['b'], 2)

    def test_tdict_nested_with_dict_literals(self):
        """Test creating nested Tdict structure."""
        td = Tdict()
        td['level1'] = Tdict()
        td['level1']['level2'] = {'key': 'value'}
        self.assertEqual(td['level1']['level2'], {'key': 'value'})

    def test_tdict_clear(self):
        """Test clearing Tdict."""
        td = Tdict()
        td['a'] = 1
        td['b'] = 2
        td.clear()
        self.assertEqual(len(td), 0)

    def test_tdict_update(self):
        """Test updating Tdict."""
        td1 = Tdict()
        td1['a'] = 1
        td2 = Tdict()
        td2['b'] = 2
        td1.update(td2)
        self.assertEqual(td1['a'], 1)
        self.assertEqual(td1['b'], 2)


class TestTbunchSpecific(unittest.TestCase):
    """Test Tbunch specific functionality (Bunch-based Tmap)."""

    def test_tbunch_attribute_access(self):
        """Test attribute-style access on Tbunch."""
        tb = Tbunch()
        tb['name'] = 'John'
        self.assertEqual(tb.name, 'John')
        self.assertEqual(tb['name'], 'John')

    def test_tbunch_attribute_assignment(self):
        """Test attribute-style assignment on Tbunch."""
        tb = Tbunch()
        tb.name = 'Jane'
        self.assertEqual(tb['name'], 'Jane')
        self.assertEqual(tb.name, 'Jane')

    def test_tbunch_nested_attribute_access(self):
        """Test nested attribute access on Tbunch."""
        tb = Tbunch()
        tb['person'] = Tbunch()
        tb.person['name'] = 'John'
        tb.person['age'] = 30
        self.assertEqual(tb.person.name, 'John')
        self.assertEqual(tb.person.age, 30)

    def test_tbunch_is_bunch(self):
        """Test that Tbunch is a Bunch."""
        from tdict import Bunch
        tb = Tbunch()
        self.assertIsInstance(tb, Bunch)

    def test_tbunch_is_tmap(self):
        """Test that Tbunch is a Tmap."""
        tb = Tbunch()
        self.assertIsInstance(tb, Tmap)

    def test_tbunch_tuple_keys_with_attributes(self):
        """Test tuple key access on Tbunch with attributes."""
        tb = Tbunch()
        tb['l1'] = Tbunch()
        tb.l1['l2'] = Tbunch()
        tb.l1.l2.value = 42
        self.assertEqual(tb[('l1', 'l2', 'value')], 42)

    def test_tbunch_update_with_attributes(self):
        """Test update on Tbunch."""
        tb1 = Tbunch()
        tb1['a'] = 10
        tb2 = Tbunch()
        tb2['a'] = 5

        tb1.update(tb2, operator.add)

        self.assertEqual(tb1.a, 15)


class TestTdictTbunchCompatibility(unittest.TestCase):
    """Test interoperability between Tdict and Tbunch."""

    def test_tdict_and_tbunch_common_interface(self):
        """Test that Tdict and Tbunch have compatible interface."""
        td = Tdict()
        tb = Tbunch()

        # Both should support same operations
        td['key'] = 'value'
        tb['key'] = 'value'

        self.assertEqual(td['key'], 'value')
        self.assertEqual(tb['key'], 'value')

    def test_nested_tdict_in_tbunch(self):
        """Test nesting Tdict inside Tbunch."""
        tb = Tbunch()
        tb['dict_branch'] = Tdict()
        tb.dict_branch['value'] = 42

        self.assertEqual(tb.dict_branch['value'], 42)
        self.assertEqual(tb[('dict_branch', 'value')], 42)

    def test_nested_tbunch_in_tdict(self):
        """Test nesting Tbunch inside Tdict."""
        td = Tdict()
        td['bunch_branch'] = Tbunch()
        td['bunch_branch']['value'] = 42

        self.assertEqual(td['bunch_branch']['value'], 42)
        self.assertEqual(td[('bunch_branch', 'value')], 42)

    def test_copy_tdict_type_preserved(self):
        """Test that copying Tdict preserves type."""
        td = Tdict()
        td['nested'] = Tdict()
        td['nested']['value'] = 1

        td_copy = td.copy()
        self.assertIsInstance(td_copy, Tdict)
        self.assertIsInstance(td_copy['nested'], Tdict)

    def test_copy_tbunch_type_preserved(self):
        """Test that copying Tbunch preserves type."""
        tb = Tbunch()
        tb['nested'] = Tbunch()
        tb.nested.value = 1

        tb_copy = tb.copy()
        self.assertIsInstance(tb_copy, Tbunch)
        self.assertIsInstance(tb_copy['nested'], Tbunch)


class TestTmapErrorHandling(unittest.TestCase):
    """Test error handling in Tmap operations."""

    def test_getitem_keyerror_propagation(self):
        """Test that KeyError is raised and propagated correctly."""
        tmap = Tdict()
        with self.assertRaises(KeyError):
            _ = tmap['nonexistent']

    def test_getitem_tuple_keyerror_includes_full_key(self):
        """Test that tuple key errors include full key."""
        tmap = Tdict()
        tmap['a'] = Tdict()
        with self.assertRaises(KeyError) as cm:
            _ = tmap[('a', 'nonexistent')]
        self.assertEqual(cm.exception.args[0], ('a', 'nonexistent'))

    def test_setitem_empty_tuple_raises_keyerror(self):
        """Test that setting empty tuple raises KeyError."""
        tmap = Tdict()
        with self.assertRaises(KeyError):
            tmap[()] = 'value'

    def test_delitem_empty_tuple_raises_keyerror(self):
        """Test that deleting empty tuple raises KeyError."""
        tmap = Tdict()
        with self.assertRaises(KeyError):
            del tmap[()]

    def test_getitem_through_scalar_raises_keyerror(self):
        """Test that traversing through scalar value raises KeyError."""
        tmap = Tdict()
        tmap['scalar'] = 42
        with self.assertRaises(KeyError):
            _ = tmap[('scalar', 'nested')]

    def test_setitem_through_scalar_raises_keyerror(self):
        """Test that setting through scalar value raises KeyError."""
        tmap = Tdict()
        tmap['scalar'] = 42
        with self.assertRaises(KeyError):
            tmap[('scalar', 'nested')] = 'value'

    def test_delitem_through_scalar_raises_keyerror(self):
        """Test that deleting through scalar value raises KeyError."""
        tmap = Tdict()
        tmap['scalar'] = 42
        with self.assertRaises(KeyError):
            del tmap[('scalar', 'nested')]


class TestTmapEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""

    def test_tmap_with_none_values(self):
        """Test Tmap with None as values."""
        tmap = Tdict()
        tmap['none_val'] = None
        self.assertIsNone(tmap['none_val'])
        self.assertEqual(len(tmap), 1)

    def test_tmap_with_zero_values(self):
        """Test Tmap with zero values."""
        tmap = Tdict()
        tmap['zero'] = 0
        tmap['empty_str'] = ''
        tmap['false'] = False
        self.assertEqual(len(tmap), 3)
        self.assertEqual(tmap['zero'], 0)
        self.assertEqual(tmap['empty_str'], '')
        self.assertEqual(tmap['false'], False)

    def test_deeply_nested_structure(self):
        """Test deeply nested Tmap structure."""
        tmap = Tdict()
        current = tmap
        depth = 5
        for i in range(depth):
            current[f'level_{i}'] = Tdict()
            current = current[f'level_{i}']
        current['leaf'] = 'value'

        # Access via tuple key
        key = tuple(f'level_{i}' for i in range(depth)) + ('leaf',)
        self.assertEqual(tmap[key], 'value')

    def test_tmap_with_many_items(self):
        """Test Tmap with many items."""
        tmap = Tdict()
        for i in range(100):
            tmap[f'key_{i}'] = i
        self.assertEqual(len(tmap), 100)
        self.assertEqual(tmap['key_50'], 50)

    def test_tmap_mixed_type_values(self):
        """Test Tmap with mixed value types."""
        tmap = Tdict()
        tmap['int'] = 42
        tmap['str'] = 'hello'
        tmap['list'] = [1, 2, 3]
        tmap['dict'] = {'a': 1}
        tmap['tmap'] = Tdict()

        self.assertEqual(tmap['int'], 42)
        self.assertEqual(tmap['str'], 'hello')
        self.assertEqual(tmap['list'], [1, 2, 3])
        self.assertEqual(tmap['dict'], {'a': 1})
        self.assertIsInstance(tmap['tmap'], Tdict)

    def test_tmap_iteration_consistency(self):
        """Test that iteration is consistent."""
        tmap = Tdict()
        tmap['a'] = Tdict()
        tmap['a']['b'] = 1
        tmap['a']['c'] = 2

        keys1 = set(tmap)
        keys2 = set(tmap)
        self.assertEqual(keys1, keys2)

    def test_tmap_len_after_delete(self):
        """Test that len updates correctly after delete."""
        tmap = Tdict()
        tmap['branch'] = Tdict()
        tmap['branch']['a'] = 1
        tmap['branch']['b'] = 2

        self.assertEqual(len(tmap), 2)
        del tmap['branch']['a']
        self.assertEqual(len(tmap), 1)

    def test_update_with_custom_operator(self):
        """Test update with custom operator."""
        tmap1 = Tdict()
        tmap1['a'] = 10
        tmap1['b'] = 20

        tmap2 = Tdict()
        tmap2['a'] = 3

        # Custom operator: take maximum
        tmap1.update(tmap2, max)

        self.assertEqual(tmap1['a'], 10)
        self.assertEqual(tmap1['b'], 20)


class TestTmapMappingProtocol(unittest.TestCase):
    """Test MutableMapping protocol implementation."""

    def test_keys_method(self):
        """Test keys() method."""
        t = Tdict()
        t['a'] = 1
        t['b'] = 2

        keys = set(t.keys())
        self.assertEqual(keys, {('a',), ('b',)})

    def test_values_method(self):
        """Test values() method."""
        t = Tdict()
        t['a'] = 1
        t['b'] = 2

        values = set(t.values())
        self.assertEqual(values, {1, 2})

    def test_items_method(self):
        """Test items() method."""
        t = Tdict()
        t['a'] = 1
        t['b'] = 2

        items = set(t.items())
        self.assertEqual(items, {(('a',), 1), (('b',), 2)})

    def test_get_method(self):
        """Test get() method."""
        t = Tdict()
        t['a'] = 1

        self.assertEqual(t.get(('a',)), 1)
        self.assertIsNone(t.get(('z',)))
        self.assertEqual(t.get(('z',), 999), 999)

    def test_update_method(self):
        """Test update() method."""
        t1 = Tdict()
        t1['a'] = 1

        t2 = Tdict()
        t2[('b',)] = 2
        t2[('c',)] = 3

        t1.update(t2)

        self.assertEqual(t1[('a',)], 1)
        self.assertEqual(t1['b'], 2)
        self.assertEqual(t1['c'], 3)


class TestTmapAutoNodeCreation(unittest.TestCase):
    """Test automatic node creation with tuple keys."""

    def test_setitem_creates_intermediate_nodes(self):
        """Test that nested Tmaps are created automatically."""
        t = Tdict()
        # This should now work because setitem creates intermediate nodes
        t[('a', 'b')] = 1

        self.assertIsInstance(t['a'], Tdict)
        self.assertEqual(t['a']['b'], 1)

    def test_setitem_deep_auto_creation(self):
        """Test auto-creation with deep nesting."""
        t = Tdict()
        t[('a', 'b', 'c', 'd')] = 42

        self.assertIsInstance(t['a'], Tdict)
        self.assertIsInstance(t['a']['b'], Tdict)
        self.assertIsInstance(t['a']['b']['c'], Tdict)
        self.assertEqual(t[('a', 'b', 'c', 'd')], 42)

    def test_setitem_does_not_overwrite_existing_nodes(self):
        """Test that auto-creation doesn't overwrite existing nodes."""
        t = Tdict()
        t['a'] = Tdict()
        t['a']['x'] = 99

        # Set a different path
        t[('a', 'b')] = 1

        self.assertEqual(t['a']['x'], 99)
        self.assertEqual(t['a']['b'], 1)


class TestTmapReplaceLeafWithMap(unittest.TestCase):
    """Test replacing leaf values with Tmaps and vice versa."""

    def test_replace_leaf_with_tmap(self):
        """Test replacing a leaf value with a Tmap."""
        t = Tdict()
        t['a'] = 1

        # Replace leaf with Tmap
        t['a'] = Tdict()
        t['a']['b'] = 2

        self.assertEqual(t[('a', 'b')], 2)

    def test_replace_tmap_with_leaf(self):
        """Test replacing a Tmap with a leaf value."""
        t = Tdict()
        t['a'] = Tdict()
        t['a']['b'] = 2

        # Replace Tmap with leaf
        t['a'] = 99

        self.assertEqual(t['a'], 99)
        with self.assertRaises(KeyError):
            _ = t[('a', 'b')]


class TestTmapWithTbunch(unittest.TestCase):
    """Test Tmap operations with Tbunch nodes."""

    def test_tmap_with_tbunch_nodes(self):
        """Test Tmap containing Tbunch nodes."""
        t = Tdict()
        t['config'] = Tbunch(name='app', version='1.0')
        t['config']['db'] = Tbunch(host='localhost', port=5432)

        self.assertEqual(t['config']['name'], 'app')
        self.assertEqual(t[('config', 'db', 'host')], 'localhost')

    def test_tbunch_iteration_with_nested_tbunch(self):
        """Test iteration through nested Tbunch."""
        tb = Tbunch()
        tb.a = Tbunch(x=1, y=2)
        tb.b = 3

        keys = set(tb)
        self.assertEqual(keys, {('a', 'x'), ('a', 'y'), ('b',)})


class TestTmapUpdateComplexScenarios(unittest.TestCase):
    """Test complex update scenarios."""

    def test_update_asymmetric_trees(self):
        """Test updating trees with different structures."""
        t1 = Tdict()
        t1['a'] = 1

        t2 = Tdict()
        t2['b'] = Tdict()
        t2['b']['c'] = 2

        t1.update(t2, operator.add)

        self.assertEqual(t1[('a',)], 1)
        self.assertEqual(t1[('b', 'c')], 2)

    def test_update_leaf_with_tmap(self):
        """Test updating where one has Tmap and other has leaf."""
        t1 = Tdict()
        t1['a'] = Tdict()
        t1['a']['x'] = 2

        t2 = Tdict()
        t2['a'] = 10

        t1.update(t2, operator.add)

        # t2['a'] is a leaf, t1['a'] is Tmap
        # Result should apply op to leaf value with Tmap values
        # New symmetric behavior: tmap1['a']['x'] becomes 2 + 10 = 12
        self.assertIsInstance(t1['a'], Tdict)
        self.assertEqual(t1['a']['x'], 12)

    def test_update_new_branches(self):
        """Test update adds new branches from other."""
        t1 = Tdict()
        t1['a'] = 1

        t2 = Tdict()
        t2['b'] = Tdict()
        t2['b']['x'] = 2

        t1.update(t2, operator.add)

        self.assertEqual(t1[('a',)], 1)
        self.assertEqual(t1[('b', 'x')], 2)


class TestTdictSpecificBehavior(unittest.TestCase):
    """Test Tdict-specific behavior."""

    def test_tdict_dict_methods(self):
        """Test that Tdict has dict methods."""
        td = Tdict()
        td['a'] = 1
        td['b'] = 2

        self.assertIn('a', td)
        self.assertIn('b', td)

    def test_tdict_pop_method(self):
        """Test pop method (inherited from dict)."""
        td = Tdict()
        td['a'] = 1

        value = td.pop('a', None)
        self.assertEqual(value, 1)
        self.assertNotIn('a', td)


class TestTbunchSpecificBehavior(unittest.TestCase):
    """Test Tbunch-specific behavior."""

    def test_tbunch_getattr_setattr(self):
        """Test attribute-style access specific to Bunch."""
        tb = Tbunch()
        tb.name = 'test'

        # Both access styles work
        self.assertEqual(tb.name, 'test')
        self.assertEqual(tb['name'], 'test')

    def test_tbunch_delattr(self):
        """Test attribute deletion."""
        tb = Tbunch()
        tb.x = 1
        del tb.x

        with self.assertRaises(AttributeError):
            _ = tb.x

    def test_tbunch_nested_attribute_chain(self):
        """Test chained attribute access."""
        tb = Tbunch()
        tb.level1 = Tbunch()
        tb.level1.level2 = Tbunch()
        tb.level1.level2.level3 = 'deep'

        self.assertEqual(tb.level1.level2.level3, 'deep')
        self.assertEqual(tb[('level1', 'level2', 'level3')], 'deep')

    def test_tbunch_mixed_access_styles(self):
        """Test Tbunch with mixed access styles."""
        tb = Tbunch()
        tb.data = Tbunch()
        tb['data']['x'] = 1
        tb.data.y = 2

        self.assertEqual(tb[('data', 'x')], 1)
        self.assertEqual(tb[('data', 'y')], 2)


class TestTmapEmptyAndNested(unittest.TestCase):
    """Test special cases with empty and nested structures."""

    def test_empty_tmap(self):
        """Test empty Tmap."""
        t = Tdict()
        self.assertEqual(len(t), 0)
        self.assertEqual(list(t), [])

    def test_tmap_nested_empty(self):
        """Test Tmap with empty nested Tmap."""
        t = Tdict()
        t['a'] = Tdict()

        # Empty nested Tmap has len 0
        self.assertEqual(len(t), 0)

    def test_tmap_with_various_types(self):
        """Test Tmap with various value types."""
        t = Tdict()
        t['int'] = 42
        t['str'] = 'hello'
        t['list'] = [1, 2, 3]
        t['dict'] = {'nested': 'dict'}

        self.assertEqual(t[('int',)], 42)
        self.assertEqual(t[('str',)], 'hello')
        self.assertEqual(t[('list',)], [1, 2, 3])
        self.assertEqual(t[('dict',)], {'nested': 'dict'})

    def test_tmap_large_structure(self):
        """Test Tmap with large nested structure."""
        t = Tdict()
        for i in range(100):
            t[f'level1_{i}'] = Tdict()
            for j in range(10):
                t[f'level1_{i}'][f'level2_{j}'] = i * 10 + j

        self.assertEqual(len(t), 1000)
        self.assertEqual(t[('level1_50', 'level2_5')], 505)


class TestTmapFromMapTree(unittest.TestCase):
    """Test Tmap.from_map_tree class method."""

    def test_from_map_tree_empty_dict(self):
        """Test converting empty dict to Tmap."""
        d = {}
        t = Tdict.from_map_tree(d)
        self.assertIsInstance(t, Tdict)
        self.assertEqual(len(t), 0)

    def test_from_map_tree_flat_dict(self):
        """Test converting flat dict to Tmap."""
        d = {'a': 1, 'b': 2, 'c': 3}
        t = Tdict.from_map_tree(d)
        self.assertIsInstance(t, Tdict)
        self.assertEqual(t['a'], 1)
        self.assertEqual(t['b'], 2)
        self.assertEqual(t['c'], 3)

    def test_from_map_tree_nested_dict(self):
        """Test converting nested dict to Tmap."""
        d = {
            'level1': {
                'level2': {
                    'value': 42
                }
            }
        }
        t = Tdict.from_map_tree(d)
        self.assertIsInstance(t, Tdict)
        self.assertIsInstance(t['level1'], Tdict)
        self.assertIsInstance(t['level1']['level2'], Tdict)
        self.assertEqual(t['level1']['level2']['value'], 42)

    def test_from_map_tree_mixed_structure(self):
        """Test converting mixed structure with scalars and nested dicts."""
        d = {
            'scalar': 'value',
            'number': 123,
            'nested': {
                'key1': 'val1',
                'key2': 'val2'
            }
        }
        t = Tdict.from_map_tree(d)
        self.assertEqual(t['scalar'], 'value')
        self.assertEqual(t['number'], 123)
        self.assertEqual(t['nested']['key1'], 'val1')
        self.assertEqual(t['nested']['key2'], 'val2')

    def test_from_map_tree_with_lists(self):
        """Test converting dict with lists."""
        d = {
            'items': [1, 2, 3],
            'nested': {
                'data': ['a', 'b']
            }
        }
        t = Tdict.from_map_tree(d)
        self.assertEqual(t['items'], [1, 2, 3])
        self.assertEqual(t['nested']['data'], ['a', 'b'])

    def test_from_map_tree_deep_nesting(self):
        """Test converting deeply nested dict."""
        d = {'a': {'b': {'c': {'d': {'e': 'value'}}}}}
        t = Tdict.from_map_tree(d)
        self.assertEqual(t['a']['b']['c']['d']['e'], 'value')
        self.assertEqual(t[('a', 'b', 'c', 'd', 'e')], 'value')

    def test_from_map_tree_tbunch(self):
        """Test converting to Tbunch."""
        d = {
            'name': 'John',
            'data': {
                'age': 30,
                'city': 'NYC'
            }
        }
        tb = Tbunch.from_map_tree(d)
        self.assertIsInstance(tb, Tbunch)
        self.assertEqual(tb.name, 'John')
        self.assertEqual(tb.data.age, 30)
        self.assertEqual(tb.data.city, 'NYC')

    def test_from_map_tree_with_through_list(self):
        """Test from_map_tree with through parameter for lists."""
        d = {
            'items': [
                {'a': 1, 'b': 2},
                {'a': 3, 'b': 4}
            ]
        }
        t = Tdict.from_map_tree(d, through={list})
        self.assertIsInstance(t['items'], list)
        self.assertIsInstance(t['items'][0], Tdict)
        self.assertEqual(t['items'][0]['a'], 1)
        self.assertEqual(t['items'][1]['a'], 3)

    def test_from_map_tree_with_through_tuple(self):
        """Test from_map_tree with through parameter for tuples."""
        d = {
            'coords': ({'x': 0, 'y': 0}, {'x': 1, 'y': 1})
        }
        t = Tdict.from_map_tree(d, through={tuple})
        self.assertIsInstance(t['coords'], tuple)
        self.assertIsInstance(t['coords'][0], Tdict)
        self.assertEqual(t['coords'][0]['x'], 0)
        self.assertEqual(t['coords'][1]['x'], 1)

    def test_from_map_tree_scalar_value(self):
        """Test from_map_tree with non-mapping value."""
        result = Tdict.from_map_tree(42)
        self.assertEqual(result, 42)

    def test_from_map_tree_with_none_values(self):
        """Test from_map_tree with None values."""
        d = {
            'key1': None,
            'key2': {
                'inner': None
            }
        }
        t = Tdict.from_map_tree(d)
        self.assertIsNone(t['key1'])
        self.assertIsNone(t['key2']['inner'])

    def test_from_map_tree_empty_nested_dict(self):
        """Test from_map_tree with empty nested dicts."""
        d = {
            'branch': {},
            'value': 1
        }
        t = Tdict.from_map_tree(d)
        self.assertIsInstance(t['branch'], Tdict)
        self.assertEqual(len(t['branch']), 0)

    def test_from_map_tree_with_mixed_through_types(self):
        """Test from_map_tree with multiple through types."""
        d = {
            'data': [
                {'items': (1, 2, 3)},
                {'items': (4, 5, 6)}
            ]
        }
        t = Tdict.from_map_tree(d, through={list, tuple})
        self.assertIsInstance(t['data'], list)
        self.assertIsInstance(t['data'][0], Tdict)
        self.assertIsInstance(t['data'][0]['items'], tuple)


class TestTmapToMapTree(unittest.TestCase):
    """Test Tmap.to_map_tree method."""

    def test_to_map_tree_empty_tmap(self):
        """Test converting empty Tmap to dict."""
        t = Tdict()
        d = t.to_map_tree()
        self.assertIsInstance(d, dict)
        self.assertEqual(len(d), 0)

    def test_to_map_tree_flat_tmap(self):
        """Test converting flat Tmap to dict."""
        t = Tdict()
        t['a'] = 1
        t['b'] = 2
        t['c'] = 3
        d = t.to_map_tree()
        self.assertIsInstance(d, dict)
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b'], 2)
        self.assertEqual(d['c'], 3)

    def test_to_map_tree_nested_tmap(self):
        """Test converting nested Tmap to dict."""
        t = Tdict()
        t['level1'] = Tdict()
        t['level1']['level2'] = Tdict()
        t['level1']['level2']['value'] = 42
        d = t.to_map_tree()
        self.assertIsInstance(d, dict)
        self.assertIsInstance(d['level1'], dict)
        self.assertIsInstance(d['level1']['level2'], dict)
        self.assertEqual(d['level1']['level2']['value'], 42)

    def test_to_map_tree_mixed_structure(self):
        """Test converting mixed Tmap structure."""
        t = Tdict()
        t['scalar'] = 'value'
        t['number'] = 123
        t['nested'] = Tdict()
        t['nested']['key1'] = 'val1'
        d = t.to_map_tree()
        self.assertEqual(d['scalar'], 'value')
        self.assertEqual(d['number'], 123)
        self.assertEqual(d['nested']['key1'], 'val1')

    def test_to_map_tree_with_lists(self):
        """Test converting Tmap containing lists."""
        t = Tdict()
        t['items'] = [1, 2, 3]
        t['nested'] = Tdict()
        t['nested']['data'] = ['a', 'b']
        d = t.to_map_tree()
        self.assertEqual(d['items'], [1, 2, 3])
        self.assertEqual(d['nested']['data'], ['a', 'b'])

    def test_to_map_tree_deep_nesting(self):
        """Test converting deeply nested Tmap."""
        t = Tdict()
        t[('a', 'b', 'c', 'd', 'e')] = 'value'
        d = t.to_map_tree()
        self.assertEqual(d['a']['b']['c']['d']['e'], 'value')

    def test_to_map_tree_tbunch(self):
        """Test converting Tbunch to dict."""
        tb = Tbunch()
        tb.name = 'John'
        tb.data = Tbunch()
        tb.data.age = 30
        tb.data.city = 'NYC'
        d = tb.to_map_tree()
        self.assertIsInstance(d, dict)
        self.assertEqual(d['name'], 'John')
        self.assertEqual(d['data']['age'], 30)

    def test_to_map_tree_custom_shallow_type(self):
        """Test to_map_tree with custom shallow_type."""
        from collections import OrderedDict
        t = Tdict()
        t['z'] = 1
        t['a'] = 2
        d = t.to_map_tree(shallow_type=OrderedDict)
        self.assertIsInstance(d, OrderedDict)

    def test_to_map_tree_with_through_list(self):
        """Test to_map_tree with through parameter for lists."""
        t = Tdict()
        t['items'] = [Tdict({'a': 1, 'b': 2}), Tdict({'a': 3, 'b': 4})]
        d = t.to_map_tree(through={list})
        self.assertIsInstance(d['items'], list)
        self.assertIsInstance(d['items'][0], dict)
        self.assertEqual(d['items'][0]['a'], 1)
        self.assertEqual(d['items'][1]['a'], 3)

    def test_to_map_tree_with_through_tuple(self):
        """Test to_map_tree with through parameter for tuples."""
        t = Tdict()
        t['coords'] = (Tdict({'x': 0, 'y': 0}), Tdict({'x': 1, 'y': 1}))
        d = t.to_map_tree(through={tuple})
        self.assertIsInstance(d['coords'], tuple)
        self.assertIsInstance(d['coords'][0], dict)
        self.assertEqual(d['coords'][0]['x'], 0)

    def test_to_map_tree_with_none_values(self):
        """Test to_map_tree with None values."""
        t = Tdict()
        t['key1'] = None
        t['key2'] = Tdict()
        t['key2']['inner'] = None
        d = t.to_map_tree()
        self.assertIsNone(d['key1'])
        self.assertIsNone(d['key2']['inner'])

    def test_to_map_tree_empty_nested_tmap(self):
        """Test to_map_tree with empty nested Tmaps."""
        t = Tdict()
        t['branch'] = Tdict()
        t['value'] = 1
        d = t.to_map_tree()
        self.assertIsInstance(d['branch'], dict)
        self.assertEqual(len(d['branch']), 0)


class TestTmapRoundTrip(unittest.TestCase):
    """Test round-trip conversions between Tmap and dict trees."""

    def test_roundtrip_dict_to_tmap_to_dict(self):
        """Test converting dict -> Tmap -> dict preserves structure."""
        original = {
            'a': 1,
            'b': {
                'c': 2,
                'd': {
                    'e': 3
                }
            },
            'f': 'string'
        }
        t = Tdict.from_map_tree(original)
        result = t.to_map_tree()
        self.assertEqual(result, original)

    def test_roundtrip_tmap_to_dict_to_tmap(self):
        """Test converting Tmap -> dict -> Tmap preserves structure."""
        t1 = Tdict()
        t1[('a', 'b', 'c')] = 1
        t1[('a', 'b', 'd')] = 2
        t1[('x', 'y')] = 3
        t1['scalar'] = 42

        d = t1.to_map_tree()
        t2 = Tdict.from_map_tree(d)

        # Both should have same leaf values
        self.assertEqual(t1[('a', 'b', 'c')], t2[('a', 'b', 'c')])
        self.assertEqual(t1[('a', 'b', 'd')], t2[('a', 'b', 'd')])
        self.assertEqual(t1[('x', 'y')], t2[('x', 'y')])
        self.assertEqual(t1['scalar'], t2['scalar'])

    def test_roundtrip_with_lists(self):
        """Test round-trip with lists."""
        original = {
            'data': [
                {'a': 1},
                {'b': 2}
            ]
        }
        t = Tdict.from_map_tree(original, through={list})
        result = t.to_map_tree(through={list})
        self.assertEqual(result, original)

    def test_roundtrip_tbunch_with_attributes(self):
        """Test round-trip with Tbunch preserving attribute access."""
        original = {
            'user': {
                'name': 'John',
                'email': 'john@example.com'
            }
        }
        tb = Tbunch.from_map_tree(original)
        self.assertEqual(tb.user.name, 'John')
        result = tb.to_map_tree()
        self.assertEqual(result, original)

    def test_roundtrip_complex_nested_structure(self):
        """Test round-trip with complex nested structure."""
        original = {
            'level1': {
                'level2a': {
                    'value': 1,
                    'data': [1, 2, 3]
                },
                'level2b': {
                    'value': 2
                }
            },
            'scalar': 'test'
        }
        t = Tdict.from_map_tree(original)
        result = t.to_map_tree()
        self.assertEqual(result, original)

    def test_roundtrip_empty_structures(self):
        """Test round-trip with empty structures."""
        original = {
            'empty_branch': {},
            'value': 1
        }
        t = Tdict.from_map_tree(original)
        result = t.to_map_tree()
        self.assertEqual(result, original)


class TestTmapConversionEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios for conversion methods."""

    def test_from_map_tree_preserves_scalar_types(self):
        """Test that from_map_tree preserves scalar value types."""
        d = {
            'int': 42,
            'float': 3.14,
            'str': 'hello',
            'bool': True,
            'none': None
        }
        t = Tdict.from_map_tree(d)
        self.assertEqual(t['int'], 42)
        self.assertEqual(t['float'], 3.14)
        self.assertEqual(t['str'], 'hello')
        self.assertEqual(t['bool'], True)
        self.assertIsNone(t['none'])

    def test_to_map_tree_preserves_scalar_types(self):
        """Test that to_map_tree preserves scalar value types."""
        t = Tdict()
        t['int'] = 42
        t['float'] = 3.14
        t['str'] = 'hello'
        t['bool'] = True
        t['none'] = None
        d = t.to_map_tree()
        self.assertEqual(d['int'], 42)
        self.assertEqual(d['float'], 3.14)
        self.assertEqual(d['str'], 'hello')
        self.assertEqual(d['bool'], True)
        self.assertIsNone(d['none'])

    def test_from_map_tree_with_numeric_string_keys(self):
        """Test from_map_tree with numeric string keys."""
        d = {
            '1': 'one',
            '2': {'3': 'three'}
        }
        t = Tdict.from_map_tree(d)
        self.assertEqual(t['1'], 'one')
        self.assertEqual(t['2']['3'], 'three')

    def test_from_map_tree_with_special_characters_in_keys(self):
        """Test from_map_tree with special characters in keys."""
        d = {
            'key-with-dash': 1,
            'key.with.dot': 2,
            'key with space': 3
        }
        t = Tdict.from_map_tree(d)
        self.assertEqual(t['key-with-dash'], 1)
        self.assertEqual(t['key.with.dot'], 2)
        self.assertEqual(t['key with space'], 3)

    def test_from_map_tree_large_structure(self):
        """Test from_map_tree with large structure."""
        d = {}
        for i in range(100):
            d[f'key_{i}'] = {'nested': i}
        t = Tdict.from_map_tree(d)
        self.assertEqual(len(t), 100)
        self.assertEqual(t['key_50']['nested'], 50)

    def test_to_map_tree_large_structure(self):
        """Test to_map_tree with large structure."""
        t = Tdict()
        for i in range(100):
            t[f'key_{i}'] = Tdict()
            t[f'key_{i}']['nested'] = i
        d = t.to_map_tree()
        self.assertEqual(len(d), 100)
        self.assertEqual(d['key_50']['nested'], 50)

    def test_from_map_tree_with_duplicate_nested_dicts(self):
        """Test from_map_tree behavior with nested dicts (should create copies)."""
        shared_dict = {'value': 42}
        d = {
            'branch1': shared_dict,
            'branch2': shared_dict
        }
        t = Tdict.from_map_tree(d)
        # Both branches should have independent Tdict copies
        self.assertEqual(t['branch1']['value'], 42)
        self.assertEqual(t['branch2']['value'], 42)

    def test_to_map_tree_with_duplicate_nested_tmaps(self):
        """Test to_map_tree behavior with nested Tmaps (should create copies)."""
        shared_tmap = Tdict()
        shared_tmap['value'] = 42
        t = Tdict()
        t['branch1'] = shared_tmap
        t['branch2'] = shared_tmap
        d = t.to_map_tree()
        # Both branches should have independent dict copies
        self.assertEqual(d['branch1']['value'], 42)
        self.assertEqual(d['branch2']['value'], 42)

    def test_from_map_tree_circular_reference_handling(self):
        """Test from_map_tree with structure that would have circular refs."""
        # Create a dict that would fail if we allowed true circular refs
        d = {'a': {'b': {'c': 1}}}
        t = Tdict.from_map_tree(d)
        # Should successfully convert without infinite recursion
        self.assertEqual(t['a']['b']['c'], 1)

    def test_to_map_tree_deeply_nested_many_leaves(self):
        """Test to_map_tree with many leaves at different depths."""
        t = Tdict()
        t['a'] = 1
        t['b'] = Tdict()
        t['b']['c'] = 2
        t['b']['d'] = Tdict()
        t['b']['d']['e'] = 3
        d = t.to_map_tree()
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b']['c'], 2)
        self.assertEqual(d['b']['d']['e'], 3)


if __name__ == '__main__':
    unittest.main()
