import operator
from collections import abc
from typing import Mapping


class Tdict(abc.MutableMapping):
    """
    Tree dict.

    Values of `str` keys can be accessed either as attributes or as items.
    Values of `tuple` keys are stored in nested `Tdict`s.

    >>> d = Tdict(
            {'a': 1, 'sub': {tuple('non-str keys allowed'.split()): True}},
            json.loads('{"sub": {"x": 10}}'),
            b=2, **{'c': 3}, d=4)
    >>> d
    Tdict(a=1, sub=Tdict(('non-str', 'keys', 'allowed')=True, x=10), b=2, c=3, d=4)
    >>> assert d[()] is d
    >>> d.a
    1
    >>> d['b']
    2
    >>> d.e = 5
    >>> d['f'] = 6
    >>> 'sub' in d
    True
    >>> ('sub', 'x') in d
    True
    >>> d.sub.x
    10
    >>> d.sub.y = 11
    >>> d['sub', 'y']
    11
    >>> d |= {'g': 7}
    >>> d += {'a': 100}
    >>> d * Tdict(sub=Tdict(y=7)) + dict(sub=100)
    Tdict(a=101, sub=Tdict(('non-str', 'keys', 'allowed')=101, x=110, y=177), b=2, c=3, d=4, e=5, f=6, g=7)
    >>> list(d.items(deep=False))
    [('a', 101),
     ('sub', Tdict(('non-str', 'keys', 'allowed')=True, x=10, y=11)),
     ('b', 2),
     ('c', 3),
     ('d', 4),
     ('e', 5),
     ('f', 6),
     ('g', 7)]
    >>> len(d)
    8

    @DynamicAttrs
    """

    def __init__(self, *maps, **attr):
        """

        Args:
            *maps (Mapping): Update attributes from these `Mapping`s.
                             Values that are themselves `Mapping`s are deep-copied as sub-`Tdict`s.
            **attr: Extra attributes (not copied).
        """
        super().__init__()
        for m in maps:
            for k, v in Tdict._shallow_items(m):
                if isinstance(v, abc.Mapping):
                    vars(self).setdefault(k, Tdict()).update(v)
                else:
                    vars(self)[k] = v
        self.update(attr)

    def __getitem__(self, k):
        """

        Args:
            k: Item key. May be a `tuple` for deep access.

        Returns:
            Item value.
        """
        if isinstance(k, tuple):
            if len(k) == 0:
                return self
            elif len(k) == 1:
                return vars(self)[k[0]]
            else:
                return vars(self)[k[0]][k[1:]]
        else:
            return vars(self)[k]

    __getattr__ = __getitem__

    def __setitem__(self, k, v):
        """

        Args:
            k: Item key. May be a `tuple` for deep access, which creates nested `Tdict`s as needed.
            v: Item value.

        Raises:
            KeyError: Item key is an empty `tuple`.
        """
        if isinstance(k, tuple):
            if len(k) == 0:
                raise KeyError("cannot assign to root")
            elif len(k) == 1:
                vars(self)[k[0]] = v
            else:
                vars(self).setdefault(k[0], Tdict())[k[1:]] = v
        else:
            vars(self)[k] = v

    __setattr__ = __setitem__

    def __delitem__(self, k):
        """

        Args:
            k: Item key. May be a `tuple` for deep access.

        Raises:
            KeyError: Item key is an empty `tuple`.
        """
        if isinstance(k, tuple):
            if len(k) == 0:
                raise KeyError("cannot delete root")
            elif len(k) == 1:
                del vars(self)[k[0]]
            else:
                del vars(self)[k[0]][k[1:]]
        else:
            del vars(self)[k]

    def keys(self, deep=True):
        """

        Args:
            deep (bool)

        Yields:
            Next key.
        """
        if deep:
            for k, v in vars(self).items():
                if isinstance(v, Tdict):
                    for k_ in v.keys():
                        yield (k,) + k_
                else:
                    yield (k,)
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
                if isinstance(v, Tdict):
                    for k_, v_ in v.items():
                        yield (k,) + k_, v_
                else:
                    yield (k,), v
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
                if isinstance(v, Tdict):
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
            int: Number of leaf (non-`Tdict`) values.
        """
        return sum(len(v) if isinstance(v, Tdict) else 1 for v in self.values())

    def __repr__(self):
        """

        Returns:
            str: String representation of `self`.
        """
        return f'Tdict({", ".join(f"{k}={v!r}" for k, v in vars(self).items())})'

    def __contains__(self, k):
        """

        Args:
            k: Item key. May be a `tuple` for deep access.

        Returns:
            bool: Key existence.
        """
        if isinstance(k, tuple):
            if len(k) == 0:
                return True
            elif len(k) == 1:
                return k[0] in vars(self)
            else:
                if k[0] in vars(self):
                    return k[1:] in vars(self)[k[0]]
                else:
                    return False
        else:
            return k in vars(self)

    def copy(self):
        """

        Returns:
            Tdict: Deep copy of `self`.
        """
        res = Tdict()
        for k, v in self.items(False):
            if isinstance(v, Tdict):
                vars(res)[k] = v.copy()
            else:
                vars(res)[k] = v
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
            Tdict: `self` after update.
        """
        if isinstance(d, abc.Mapping):
            for k, v in Tdict._shallow_items(d):
                if k in vars(self):
                    v_ = vars(self)[k]
                    if isinstance(v_, Tdict):
                        if isinstance(v, abc.Mapping) or o is not None:
                            vars(self)[k].update(v, o)
                        else:
                            vars(self)[k] = v
                    elif o is None:
                        vars(self)[k] = v
                    else:
                        vars(self)[k] = o(v_, v)
                else:
                    vars(self)[k] = v
        else:
            for k, v in vars(self).items():
                if isinstance(v, Tdict):
                    v.update(d, o)
                elif o is None:
                    vars(self)[k] = d
                else:
                    vars(self)[k] = o(v, d)
        return self

    @staticmethod
    def _shallow_items(m):
        if isinstance(m, Tdict):
            return m.items(False)
        else:
            return m.items()


class _Op(object):
    def __init__(self, o, inplace=True):
        self.o = o
        self.inplace = inplace

    def __get__(self, obj, objtype=None):
        def apply(x, y):
            if not self.inplace:
                x = x.copy()
            return x.update(y, self.o)

        return apply.__get__(obj, objtype)


_OPERATORS = {
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

for name, op in _OPERATORS.items():
    setattr(Tdict, f'__{name}__', _Op(op, False))
    setattr(Tdict, f'__i{name}__', _Op(op, True))
