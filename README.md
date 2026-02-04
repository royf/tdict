# Tdict

`Tdict` is a tree-structured mapping for easy handling of configurations and results.
Compared to a tree of `dict`, item access in `Tdict` is improved in two ways:
- **Attribute access:** `Tdict` items can be accessed as attributes.
For example, you can access `config.model.layers[0].params.w`, just as well as `config['model']['layers'][0]['params']['w']`.
Many people would find the former more readable.
- **Deep access:** Nested `Tdict` items can be accessed by `tuple` keys.
For example, the above item can also be accessed by `config['model', 'layers', 0, 'params', 'w']`, which makes it easier to iterate through the tree structure.
Several helper methods simplify this access.

The main features of `Tdict` are detailed below.
We start with some definitions that clarify how to think about mapping trees.


## `Mapping` trees

A `Tdict` object is just a fancy mutable mapping with some nice helper methods.
But when nested, a `Tdict` can be thought of as a node in a tree, or the root of a subtree.

Nested `Mapping`s form a rooted `Mapping` tree, where a branch is a sequence that starts at the root object and where every following object is a value in the previous `Mapping`.
An object in the tree is called an inner node if it is a `Mapping`, otherwise a leaf node.
If all `Mapping`s in a tree are also `Tdict`s, it is called a `Tdict` tree (as opposed to just a `Tdict`, which is a node in the tree).
In some contexts, but not all, it is valid to have a degenerate `Mapping` tree that has just one non-`Mapping` node as both root and leaf.

Each node in a `Mapping` tree is uniquely defined by the sequence of keys in the path from the root to that node.
In contrast, values can be repeated across paths, but not within the same path to avoid infinite loops.
The root is identified by the empty `tuple`.
A `tuple` of keys identifying a node is called a deep key, and a prefix of the deep key identifies an ancestor of the node.
The prefix or ancestor will be called proper when it isn't the node itself.


## Initialization

- `Tdict(*map_trees, **map_tree)`

A new `Tdict` tree can be initialized from any number of non-degenerate `Mapping` trees in `map_trees`, plus one more given by `map_tree`, that are used to iteratively (in order) `update` the `Tdict` tree rooted at the new `Tdict` (see [Updating](#updating) below).
The resulting `Tdict` tree has any leaf in any map in `[*map_trees, map_tree]` that is neither a prefix of, nor prefixed by, a leaf of a later map.

Example:
```python
d = Tdict({'aa': 1, 'bb': 2, 'dd': {'ee': 5}}, {'bb': {'cc': 3}}, dd=4)
print(d)
# Tdict(aa=1, bb=Tdict(cc=3), dd=4)
```


## Class attributes

- `d.DEEP` (default: `True`)
- `d.DEFAULT_FACTORY` (default: `None`)
- `with_deep(self, deep=True)`
- `with_shallow(self, deep=False)`
- `with_default_factory(self, default_factory)`

Because the items of a `Tdict` can be accessed as if they were instance attributes, a `Tdict` cannot have instance attributes.
However, a mechanism akin to instance attributes is needed to modify the behavior of some methods whose signature cannot be changed (such as `get` and `keys`).
As a workaround, the current implementation uses class attributes for these would-be instance attributes, by creating a custom class for each new `Tdict`.
This implies that `isinstance(d, Tdict)` should always be used for type checking, as `type(d) == Tdict` and `type(d1) == type(d2)` are always False.

The two builtin attributes are `DEEP` and `DEFAULT_FACTORY`, and their semantics are explained below for the methods they affect.
These attributes should not be set directly, but through the in-place setters `with_deep`, `with_shallow`, and `with_default_factory`.
When constructing a new `Tdict` from another's constructor, e.g. `type(d)()`, these builtin attributes are initialized to the same value.

It is possible to access builtin and user-defined class attributes directly via `type(d).DEEP` etc.
Please note that setting, say, `d.DEEP` sets the value of an item with the key `DEEP`, which is distinct from the class attribute.
The same is true for class methods, such as `get`: they can be used as long as no item with key `get` is added; after that, `d.get` accesses the item, while `type(d).get` accesses the class method.
There are therefore three ways to avoid issues with the `Tdict` mechanism: (1) be sure that no keys are ever the same as class attributes that you use in your code (library code is shielded from this issue); (2) check your keys against `dir(Tdict)` before adding them; or (3) always access class attributes using `type(d)`.

Example:
```python
d = Tdict({'aa': {'bb': 2}})
print(d.DEEP, d.DEFAULT_FACTORY)
# True None
print(d.get(['DEEP', 'DEFAULT_FACTORY', 'cc']))
# Tdict()
d.DEEP = 'this is an item, not a class attribute'
d.DEFAULT_FACTORY = 'probably not what you intended to do'
d.cc = 3
d.with_shallow().with_default_factory(list)
# Tdict(aa=Tdict(bb=2), DEEP='this is an item, not a class attribute', DEFAULT_FACTORY='probably not what you intended to do', cc=3)
type(d).cc = 4
print(type(d).DEEP, type(d).DEFAULT_FACTORY, type(d).cc)
# False <class 'list'> 4
```


## Representation

- `str(d)`
- `repr(d)`

The `str` representation of a `Tdict` consists of its class name, followed in parentheses by the comma-separated shallow key–value pairs with an equal sign between them.
In the informal version, `str(d)`, the `str` of every key and value is taken, whereas the formal version, `repr(d)`, uses their `repr`, except for keys that are identifiers which appear as they are.

Example:
```python
d = Tdict(aa={'1': 'x'}, bb=2)
print(d)
# Tdict(aa=Tdict(1=x), bb=2)
print(repr(d))
# Tdict(aa=Tdict('1'='x'), bb=2)
```


## Getting values

- `d.key`
- `d['key']`
- `d['key1', 'key2']`

`Tdict` values can be retrieved via `d.key` or `d['key']`.
The former, attribute-access form only allows keys that are valid identifiers, but the latter, item-access form allows any immutable hashable key.
One special type for item access is a `tuple`, which is treated as a deep key for `Tdict` tree traversal, with an empty `tuple` returning the root and a longer `tuple` going down a `Tdict` tree path to get the value there.
An actual `tuple` key can be used by nesting it, for example `d[(1, 2, 3),]` accesses a child of the root with a `tuple` key, while `d[1, 2, 3]` accesses a great-grandchild of the root with a branch of `int` keys.
Attribute access is always shallow.

Deep access has a mechanism for adding default leaf values when they are missing, inspired by `defaultdict`: if a missing leaf's parent node has a non-`None` `DEFAULT_FACTORY` class attribute, that `DEFAULT_FACTORY` is called without arguments to get and add the leaf's value.
In this case, any missing inner nodes along the branch are also added with the same type (`Tdict` or its subclass) as the branch's last existing inner node.
A `KeyError` is raised if any inner node along the branch exists but is not a `Tdict`, or if any inner or leaf node is missing when the `DEFAULT_FACTORY` class attribute of the last existing inner node is `None`.

Example:
```python
d = Tdict({'a': Tdict(b=Tdict(c=3)), ('a', 'b', 'c'): 4})
print(d[*'abc'])
# 3
print(d[(*'abc',),])
# 4
```


## Setting values

- `d.key = val`
- `d['key'] = val`
- `d['key1', 'key2'] = val`

Setting the values of items in a `Tdict` tree is similar to getting them but with some differences.
An empty `tuple` cannot be used for setting values, because the root cannot be assigned a new value.
Deep access always adds any missing inner nodes along the branch with the same type (`Tdict` or its subclass) as the branch's last existing inner node.
A `KeyError` is raised if any inner node along the branch exists but is not a `Tdict`.

Example:
```python
d = Tdict()
d[*'abc'] = 3
print(d.a)
# Tdict(b=Tdict(c=3))
print(d['a', 'b'])
# Tdict(c=3)
d[(*'abc',),] = 4
print(d)
# Tdict(a=Tdict(b=Tdict(c=3)), ('a', 'b', 'c')=4)
```


## Deleting items

- `del d.key`
- `del d['key']`
- `del d['key1', 'key2']`

Deleting items from a `Tdict` tree is similar to getting and setting values but with some differences.
An empty `tuple` cannot be used for deleting items, because the root cannot be deleted.
Deep access does not delete inner nodes along the branch, even if they become empty.
A `KeyError` is raised if any inner or leaf node along the branch is missing or if any inner node is not a `Tdict`.

Example:
```python
d = Tdict({'a': Tdict(b=Tdict(c=3)), ('a', 'b', 'c'): 4})
del d[*'abc']
print(d)
# Tdict(a=Tdict(b=Tdict()), ('a', 'b', 'c')=4)
del d.a.b
print(d)
# Tdict(a=Tdict(), ('a', 'b', 'c')=4)
del d[(*'abc',),]
print(d)
# Tdict(a=Tdict())
```


## Membership

- `'key' in d`
- `('key1', 'key2') in d`

Membership is either checked as a shallow `Tdict` membership in the root node, or as deep `Tdict` tree membership for deep keys (i.e. `tuple`s).


## Advanced access

- `get(self, key=None, default=None, get_default=None, **keys)`
- `getdefault(self, key=None, default=None, **keys)`
- `setdefault(self, key=None, default=None, **keys)`
- `pop(self, key=None, default=None, get_default=None, **keys)`

These methods provide an advanced mechanism for getting, setting, and popping (deleting and returning) multiple items, with or without defaults.
The same semantics of shallow and deep access apply, as in the above single-item methods.
A `Sequence` key (that is not a `tuple`) is treated as multiple keys that correspond to the `default` argument.
A `Mapping` key (or `None`), and additionally any `keys`, is treated as multiple keys that correspond to the default given in their associated values.
For a single key (across `key` and `keys`), these methods return its value or default.
For multiple keys, they return a `Tdict` of the same type as `self`, including the requested values, while providing some control over the omission of missing values (after which, the number of returned values can become 0 or 1).

`get` simply returns the requested items, with defaults for missing values, except that `None` defaults are omitted when requesting multiple keys unless `get_detault` is True.
`getdefault` does not omit `None` defaults.
`setdefault` also sets the defaults of any missing values (thus no omissions).
`pop` instead deletes existing values.


## Iterators

- `keys(self, deep=None)`
- `values(self, deep=None)`
- `items(self, deep=None)`
- `iter(d)`
- `len(d)`

These methods iterate either the `Tdict` shallow keys, values, and items, respectively, or the `Tdict` tree deep keys.
The shallow vs. deep mode is determined by the class attribute `DEEP`, and can be overridden by the method's argument.
Note that a `Tdict` tree with `DEEP=True` (its default value) can have inner nodes with `DEEP=False`, in which case the mode can be mixed: deep-mode inner nodes recurse deeply through their items, while shallow-mode ones iterate over them as shallow leaves.
However, setting the argument `deep=True` overrides this behavior and iterates deeply over the entire `Tdict` tree.
The `Tdict` tree iterator is over `keys`, while `len` counts leaf `values` (with repetition), both  in the default per-node `DEEP` mode.


## Casting

- `as_dict(self)`
- `cast(cls, map_tree, through=None, op=None)`

`as_dict` simply returns the underlying `dict` of the `Tdict`.
`cast` returns a `Tdict` tree copy of a given `Mapping` tree, with `op` applied to each leaf.
It recurses over the `map_tree` through each `Mapping` node, copying it as a `Tdict` node, or as a new object of its own type if it is already a `Tdict`.
It also recurses through nodes with type in `through` (e.g. `through=[list, tuple]`) and copies them, until it reaches values that are neither a `Mapping` nor of a type in `through`.
For each such leaf, `cast` sets its value to `op(val)` of its input `val`, or to `val` if `op` is `None`.
To set the `DEEP` and `DEFAULT` of the new `Tdict` tree, its `cls` can be set accordingly, e.g. `Tdict().with_deep(False).with_default(list).cast({'a': [{'b': 2, 'c': 3}]}, [list])`.


## Copying and excluding

- `copy(self, deep=True, exclude=None)`
- `d ^ keys`
- `d ^= keys`

The `copy` method returns a copy of the `Tdict` tree (or its subclass).
As for the iterators, the `DEEP` class attribute determines the default mode and the `deep` argument can override it.
In contrast to `deepcopy` in the standard library, the deep mode of this `copy` method only traverses the `Tdict` tree, stopping at non-`Tdict` leaves.
The `exclude` argument is an iterator of keys that should be excluded from the copied object.
Whether the keys are `str` (for shallow access) or `tuple` (for deep access) must match whether copy is in deep mode or not.

`d ^ keys` is shorthand for `d.copy(deep=False, exclude=keys)`, while `d ^= keys` is shorthand for `self.pop(keys)` (but without the returned values).
Note, however, that while `pop` supports both shallow and deep access, even mixed together, `copy` does not.
Thus, `d ^ keys` returns a shallow copy of `d` with shallow `keys` excluded.


## Updating

- `update(self, other, op=None)`
- `d1 <op> d2`
- `d1 <op>= d2`

The `update` method updates the `Tdict` tree `self` from the `Mapping` tree `other`.
The logic is slightly different for the default `op`, which indicates replacement, than for any other `op`, which is more of a merge.

For the default `op`, for any deep key that is a valid path in both trees and a leaf in either of them, `other` takes precedence.
Thus, if the key leads to a leaf in `self` but a subtree in `other`, that leaf will be replaced by a `Tdict` subtree copy of the `other` subtree (with nodes that are already `Tdict` copied with the same type).
If the key leads to a leaf in `other`, the `self` subtree or leaf value will be replaced by the `other` leaf value.

For any other `op`, for any deep key that is a valid path in both trees and a leaf in either of them, we can imagine that leaf as expanded to a subtree matching the structure of the other source, with the same leaf value assigned to each new leaf.
Then the trees, which now have the same set of deep keys, are merged by taking the values `op(self_val, other_val)`.

Some special operators are defined through dunder methods to perform the corresponding update operator, both in-place and out-of-place, e.g. `d + 1` returns a new `Tdict` tree with the same deep keys and 1 to each value, while `d += 1` performs the same operator in-place.
The list of such operators is: `add`, `truediv`, `floordiv`, `pow`, `lshift`, `mod`, `mul`, `matmul`, `rshift`, and `sub`.
`xor` has the special exclusion semantics mentioned above, and `or` has the same semantics as the default (replacement) `op`, so that `d1 |= d2` updates `d1` with `d2` items, and `d1 | d2` does the same with a copy of `d1`.
The `update` method can be called directly with `operator.xor` and `operator.or` to use these missing operators.


## Subclassing

`Tdict` can be subclassed while keeping all of its behavior that is not explicitly overridden.
New `Tdict` nodes created automatically in any of the builtin methods (e.g. getting values with default, setting values, updating), will have the type of their parent node.
Care should be taken with instance attributes in a subclass of `Tdict`, as it may have the same issues mentioned under [Class attributes](#class-attributes) above.
The simplest workaround is likely to use custom class attributes instead.
