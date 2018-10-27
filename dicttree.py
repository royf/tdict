import operator
from collections import abc
from typing import Mapping


class DictTree(abc.Mapping):
    """
    Nested dict.

    Values of `str` keys can be accessed either as attributes or as items.
    Values of sub-trees can be deep-accessed by `list` keys.

    >>> d = DictTree(
            {'a': 1, ('non', 'str', 'key'): 'allowed'},
            json.loads('{"sub": {"x": 10} }'),
            b=2, **{'c': 3}, d=4)
    >>> d
    DictTree(a=1, ('non', 'str', 'key')='allowed', sub=DictTree(x=10), b=2, c=3, d=4)
    >>> assert d[[]] is d
    >>> d.a
    1
    >>> d['b']
    2
    >>> d.e = 5
    >>> d['f'] = 6
    >>> 'sub' in d
    True
    >>> ['sub', 'x'] in d
    True
    >>> d.sub.x
    10
    >>> d.sub.y = 11
    >>> d[['sub', 'y']]
    11
    >>> d |= {'g': 7}
    >>> d += {'a': 100}
    >>> d * DictTree(sub=DictTree(y=7))
    DictTree(a=101, ('non', 'str', 'key')='allowed', sub=DictTree(x=10, y=77), b=2, c=3, d=4, e=5, f=6, g=7)
    >>> list(d.items())
    [(['a'], 101),
     ([('non', 'str', 'key')], 'allowed'),
     (['sub', 'x'], 10),
     (['sub', 'y'], 11),
     (['b'], 2),
     (['c'], 3),
     (['d'], 4),
     (['e'], 5),
     (['f'], 6),
     (['g'], 7)]
    >>> list(d.items(False))
    [('a', 101),
     (('non', 'str', 'key'), 'allowed'),
     ('sub', DictTree(x=10, y=11)),
     ('b', 2),
     ('c', 3),
     ('d', 4),
     ('e', 5),
     ('f', 6),
     ('g', 7)]
    >>> len(d)
    10

    @DynamicAttrs
    """

    def __init__(self, *maps, **attr):
        """

        Args:
            *maps (Mapping): Update attributes from these `Mapping`s.
                             Values that are themselves `Mapping`s are deep-copied as sub-`DictTree`s.
            **attr: Extra attributes (not copied).
        """
        super().__init__()
        for m in maps:
            for k, v in DictTree._shallow_items(m):
                if isinstance(v, abc.Mapping):
                    self[k] = DictTree(v)
                else:
                    self[k] = v
        self.update(attr)

    def __getitem__(self, k):
        """

        Args:
            k: Item key. May be a `list` for deep access.

        Returns:
            Item value.
        """
        if isinstance(k, list):
            if len(k) == 0:
                return self
            elif len(k) == 1:
                return self[k[0]]
            else:
                return self[k[0]][k[1:]]
        else:
            return vars(self)[k]

    def setdefault(self, k, v):
        """

        Args:
            k: Item key. May be a `list` for deep access, which creates nested `DictTree`s as needed.
            v: Item value. This value is set if the item doesn't exist.

        Returns:
            Item value.

        Raises:
            KeyError: Item key is reserved.
        """
        if isinstance(k, list):
            if len(k) == 0:
                return self
            elif len(k) == 1:
                return self.setdefault(k[0], v)
            else:
                return self.setdefault(k[0], DictTree()).setdefault(k[1:], v)
        elif k in RESERVED:
            raise KeyError(f'key "{k}" is reserved')
        else:
            return vars(self).setdefault(k, v)

    def __setitem__(self, k, v):
        """

        Args:
            k: Item key. May be a `list` for deep access, which creates nested `DictTree`s as needed.
            v: Item value.

        Raises:
            KeyError: Item key is an empty `list` or reserved.
        """
        if isinstance(k, list):
            if len(k) == 0:
                raise KeyError("cannot assign to root")
            elif len(k) == 1:
                self[k[0]] = v
            else:
                self.setdefault(k[0], DictTree())[k[1:]] = v
        elif k in RESERVED:
            raise KeyError(f'key "{k}" is reserved')
        else:
            vars(self)[k] = v

    def __setattr__(self, k, v):
        self[k] = v

    def __delitem__(self, k):
        """

        Args:
            k: Item key. May be a `list` for deep access.
        """
        if isinstance(k, list):
            if len(k) == 0:
                raise KeyError("cannot delete root")
            elif len(k) == 1:
                self.__delitem__(k[0])
            else:
                self[k[0]].__delitem__(k[1:])
        else:
            vars(self).__delitem__(k)

    def keys(self, deep=True):
        """

        Args:
            deep (bool)

        Yields:
            Next key.
        """
        if deep:
            for k, v in vars(self).items():
                if isinstance(v, DictTree):
                    for k_ in v.keys():
                        yield [k] + k_
                else:
                    yield [k]
        else:
            yield from vars(self).keys()

    def items(self, deep=True):
        """

        Args:
            deep (bool)

        Yields:
            Next item.
        """
        if deep:
            for k, v in vars(self).items():
                if isinstance(v, DictTree):
                    for k_, v_ in v.items():
                        yield [k] + k_, v_
                else:
                    yield [k], v
        else:
            yield from vars(self).items()

    def values(self, deep=True):
        """

        Args:
            deep (bool)

        Yields:
            Next value.
        """
        if deep:
            for v in vars(self).values():
                if isinstance(v, DictTree):
                    yield from v.values()
                else:
                    yield v
        else:
            yield from vars(self).values()

    def __iter__(self):
        """

        Yields:
            Next key.
        """
        return self.keys()

    def __len__(self):
        """

        Returns:
            int: Number of leaf (non-`DictTree`) values.
        """
        return sum(len(v) if isinstance(v, DictTree) else 1 for v in self.values())

    def __repr__(self):
        return f'DictTree({", ".join(f"{k}={v!r}" for k, v in vars(self).items())})'

    def __contains__(self, k):
        """

        Args:
            k: Item key. May be a `list` for deep access.

        Returns:
            bool: Key existence.
        """
        if isinstance(k, list):
            if len(k) == 0:
                return True
            elif len(k) == 1:
                return k[0] in vars(self)
            else:
                if k[0] in vars(self):
                    return k[1:] in self[k[0]]
                else:
                    return False
        else:
            return k in vars(self)

    def copy(self):
        """

        Returns:
            DictTree: Deep copy of `self`.
        """
        res = DictTree()
        for k, v in self.items():
            if isinstance(v, DictTree):
                res[k] = v.copy()
            else:
                res[k] = v
        return res

    def update(self, d, o=None):
        """
        Update self from another `Mapping` or a constant.
        Update from a `Mapping` sets the values of keys of `d` that are missing in `self`,
            and applies `o` to values of shared keys.
        Update from a constant applies `o` to values of `self`.

        Args:
            d: Update from a `Mapping` or a constant.
            o ((Any, Any) -> Any): Update operator, such that `x = o(x, y)` updates value `x` with new value `y`.
                Default: replace current value, `x = y`.

        Returns:
            DictTree: `self` after update.
        """
        if isinstance(d, abc.Mapping):
            for k, v in DictTree._shallow_items(d):
                if k in vars(self):
                    if isinstance(self[k], DictTree):
                        if isinstance(v, abc.Mapping) or o is not None:
                            self[k].update(v, o)
                        else:
                            self[k] = v
                    else:
                        self[k] = o(self[k], v)
                else:
                    self[k] = v
        else:
            for k, v in vars(self).items():
                if o is None:
                    self[k] = d
                else:
                    self[k] = o(self[k], d)
        return self

    @staticmethod
    def _shallow_items(m):
        if isinstance(m, DictTree):
            return m.items(False)
        else:
            return m.items()


class Op(object):
    def __init__(self, o, inplace=True):
        self.o = o
        self.inplace = inplace

    def __get__(self, obj, objtype=None):
        def apply(x, y):
            if not self.inplace:
                x = x.copy()
            return x.update(y, self.o)

        return apply.__get__(obj, objtype)


OPERATORS = {
    'or': None,
    'add': operator.iadd,
    'truediv': operator.itruediv,
    'floordiv': operator.ifloordiv,
    'pow': operator.ipow,
    'lshift': operator.ilshift,
    'mod': operator.imod,
    'mul': operator.imul,
    'matmul': operator.imatmul,
    'rshift': operator.irshift,
    'sub': operator.isub,
}

for name, op in OPERATORS.items():
    setattr(DictTree, f'__{name}__', Op(op, False))
    setattr(DictTree, f'__i{name}__', Op(op, True))

RESERVED = set(dir(DictTree()))
