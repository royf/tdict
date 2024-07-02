import operator
from collections import abc
from functools import partial
from typing import Mapping
from typing import Sequence


class Tdict(abc.MutableMapping):
    """
    Tree dict.

    Values of `str` keys can be accessed either as attributes or as items.
    Values of `tuple` keys are stored in nested `Tdict`s.

    >>> from tdict import Tdict
    >>> import json
    >>> d = Tdict(
            {'a': 1, 'sub': {tuple('non-str keys allowed'.split()): True}},
            json.loads('{"sub": {"x": 10}}'),
            b=2, **{'c': 3}, d=4)
    >>> d
    Tdict(a=1, sub=Tdict(('non-str', 'keys', 'allowed')=True, x=10), b=2, c=3, d=4)
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
    >>> d ^= {'b'}
    >>> d += {'a': 100}
    >>> len(d)
    9
    >>> list(d.items())
    [(('a',), 101),
     (('sub', ('non-str', 'keys', 'allowed')), True),
     (('sub', 'x'), 10),
     (('sub', 'y'), 11),
     (('c',), 3),
     (('d',), 4),
     (('e',), 5),
     (('f',), 6),
     (('g',), 7)]
    >>> list(d.items(deep=False))
    [('a', 101),
     ('sub', Tdict(('non-str', 'keys', 'allowed')=True, x=10, y=11)),
     ('c', 3),
     ('d', 4),
     ('e', 5),
     ('f', 6),
     ('g', 7)]
    >>> z = d.copy()
    >>> z.set_deep(False)
    >>> assert list(z.items()) == list(d.items(deep=False)) == list(d.as_deep(False).items())
    >>> d * Tdict(sub=Tdict(y=7)) + dict(sub=100)
    Tdict(a=101, sub=Tdict(('non-str', 'keys', 'allowed')=101, x=110, y=177), c=3, d=4, e=5, f=6, g=7)
    >>> match d:  # new in Python 3.10
            case {'c': z}:
                print(z)
    3
    >>> match d:  # new in Python 3.10
            case Tdict(sub=Tdict(x=w)):
                print(w)
    10
    >>> assert d[()] is d

    @DynamicAttrs
    """

    # noinspection PyMethodParameters
    def __new__(_cls, *maps, deep=True, **attr):
        return super().__new__(type(_cls.__name__, (_cls,), {
            '_deep': deep,
            '__reduce__': lambda self: (partial(_cls.__new__, _cls, deep=deep), (), self.__dict__),
        }))

    def __init__(self, *maps, deep=True, **attr):
        """

        Args:
            *maps (Mapping): Update attributes from these `Mapping`s.
                             Values that are themselves `Mapping`s are deep-copied as sub-`Tdict`s.
            deep (bool): whether to iterate keys, values, and items recursively by default.
            **attr: Extra attributes.
        """
        super().__init__()
        for m in maps:
            shallow_map = vars(m) if isinstance(m, Tdict) else m
            for k, v in shallow_map.items():
                if isinstance(v, abc.Mapping):
                    vars(self).setdefault(k, Tdict(deep=deep)).update(v)
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
        try:
            if isinstance(k, tuple):
                if len(k) == 0:
                    return self
                else:
                    d = vars(self)[k[0]]
                    if len(k) == 1:
                        return d
                    elif isinstance(d, Tdict):
                        return vars(self)[k[0]][k[1:]]
                    else:
                        raise KeyError(k[0])
            else:
                return vars(self)[k]
        except KeyError:
            raise KeyError(k) from None

    def __setitem__(self, k, v):
        """

        Args:
            k: Item key. May be a `tuple` for deep access, which creates nested `Tdict`s as needed.
            v: Item value.

        Raises:
            KeyError: Item key is an empty `tuple`.
        """
        try:
            if isinstance(k, tuple):
                if len(k) == 0:
                    raise KeyError("cannot assign to root")
                elif len(k) == 1:
                    vars(self)[k[0]] = v
                elif k[0] not in vars(self):
                    d = Tdict(deep=self._deep)
                    d[k[1:]] = v
                    vars(self)[k[0]] = d
                elif isinstance(vars(self)[k[0]], Tdict):
                    vars(self)[k[0]][k[1:]] = v
                else:
                    raise KeyError(k[0])
            else:
                vars(self)[k] = v
        except KeyError:
            raise KeyError(k) from None

    __setattr__ = __setitem__

    def __delitem__(self, k):
        """

        Args:
            k: Item key. May be a `tuple` for deep access.

        Raises:
            KeyError: Item key is an empty `tuple`.
        """
        try:
            if isinstance(k, tuple):
                if len(k) == 0:
                    raise KeyError("cannot delete root")
                elif len(k) == 1:
                    del vars(self)[k[0]]
                elif k[0] in vars(self) and isinstance(vars(self)[k[0]], Tdict):
                    del vars(self)[k[0]][k[1:]]
                else:
                    raise KeyError(k[0])
            else:
                del vars(self)[k]
        except KeyError:
            raise KeyError(k) from None

    def set_deep(self, deep):
        type(self)._deep = deep

    def as_deep(self, deep=True):
        d = self.copy()
        d.set_deep(deep)
        return d

    def as_shallow(self, deep=False):
        return self.as_deep(deep)

    def as_dict(self):
        return vars(self)

    def keys(self, deep=None):
        """

        Args:
            deep (bool): whether to iterate recursively.

        Yields:
            Next key.
        """
        if deep or (deep is None and self._deep):
            return tdict_keys(self, deep)
        else:
            return vars(self).keys()

    def values(self, deep=None):
        """

        Args:
            deep (bool): whether to iterate recursively.

        Yields:
            Next value.
        """
        if deep or (deep is None and self._deep):
            return tdict_values(self, deep)
        else:
            return vars(self).values()

    def items(self, deep=None):
        """

        Args:
            deep (bool): whether to iterate recursively.

        Yields:
            Next item.
        """
        if deep or (deep is None and self._deep):
            return tdict_items(self, deep)
        else:
            return vars(self).items()

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
        return sum(1 for _ in self.values())

    def __repr__(self):
        """

        Returns:
            str: String representation of `self`.
        """
        return f'{type(self).__name__}({", ".join(f"{k}={v!r}" for k, v in vars(self).items())})'

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
                    d = vars(self)[k[0]]
                    return isinstance(d, Tdict) and k[1:] in d
                else:
                    return False
        else:
            return k in vars(self)

    def copy(self, exclude=None):
        """

        Args:
            exclude: Container of shallow keys to exclude. Default: no keys excluded.

        Returns:
            Tdict: Deep copy of `self`.
        """
        res = type(self)(deep=self._deep)
        for k, v in vars(self).items():
            if exclude is not None and k in exclude:
                continue
            if isinstance(v, Tdict):
                vars(res)[k] = v.copy()
            else:
                vars(res)[k] = v
        return res

    def __xor__(self, other):
        """
        Shorthand for `self.copy(exclude=other)`.

        Returns:
            Tdict: Copy of `self` with shallow keys in `other` excluded.
        """
        return self.copy(other)

    def update(self, d, o=None):
        """
        Update self from another `Mapping` or a constant.
        Update from a `Mapping` sets the values of keys of `d` that are missing in `self`,
            and applies binary operator `o(self[k], d[k])` to values of shared keys.
        Update from a constant applies `o(self[k], d)` to values of `self`.

        Args:
            d: Update from a `Mapping` or a constant.
            o ((Any, Any) -> Any): Update operator, such that `x = o(x, y)` updates value `x` with new value `y`.
                Default: replace current value, `x = y`.

        Returns:
            Tdict: `self` after update.
        """
        if isinstance(d, abc.Mapping):
            shallow_map = vars(d) if isinstance(d, Tdict) else d
            for k, v in shallow_map.items():
                if k in vars(self):
                    v_ = vars(self)[k]
                    if isinstance(v_, Tdict):
                        if isinstance(v, abc.Mapping) or o is not None:
                            vars(self)[k].update(v, o)
                        else:
                            vars(self)[k] = v
                    elif o is None:
                        vars(self)[k] = ensure_tdict(v)
                    else:
                        vars(self)[k] = o(v_, v)
                else:
                    vars(self)[k] = ensure_tdict(v)
        else:
            for k, v in vars(self).items():
                if isinstance(v, Tdict):
                    v.update(d, o)
                elif o is None:
                    vars(self)[k] = d
                else:
                    vars(self)[k] = o(v, d)
        return self


def tdict_keys(d, deep):
    for k, v in vars(d).items():
        if isinstance(v, Tdict):
            for k_ in v.keys(deep):
                # noinspection PyProtectedMember
                if deep or (deep is None and v._deep):
                    yield (k,) + k_
                else:
                    yield k, k_
        else:
            yield k,


def tdict_values(d, deep):
    for v in vars(d).values():
        if isinstance(v, Tdict):
            yield from v.values(deep)
        else:
            yield v


def tdict_items(d, deep):
    for k, v in vars(d).items():
        if isinstance(v, Tdict):
            for k_, v_ in v.items(deep):
                # noinspection PyProtectedMember
                if deep or (deep is None and v._deep):
                    yield (k,) + k_, v_
                else:
                    yield (k, k_), v_
        else:
            yield (k,), v


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
    setattr(Tdict, f'__{name}__', _Op(op, inplace=False))
    setattr(Tdict, f'__i{name}__', _Op(op, inplace=True))


def ensure_tdict(x, deep=True):
    if isinstance(x, abc.Mapping) and not isinstance(x, Tdict):
        return Tdict(x, deep=deep)
    else:
        return x


def tdictify(x, through=None, deep=True):
    """
    Return a recursively `Tdict`ified version of `x`:
        If `x` is a `Mapping`, return a `Tdict` with the same keys and `Tdict`ified values.
        If `x` is an instance of a type in `through`, return a new instance of that type with `Tdict`ified elements.
        Otherwise, return `x`.

    Args:
        x: The object to `Tdict`ify.
        through (Sequence[type]): list of types through which to deep-copy and `Tdict`ify; e.g., `[list, tuple]`.
        deep (bool): whether the constructed Tdict iterates keys, values, and items recursively by default.

    Returns:
        Tdict: `Tdict`ified version of `x`.
    """
    if isinstance(x, abc.Mapping):
        if isinstance(x, Tdict):
            # noinspection PyProtectedMember
            deep = x._deep
        shallow_map = vars(x) if isinstance(x, Tdict) else x
        return Tdict({k: tdictify(v, through, deep=deep) for k, v in shallow_map.items()}, deep=deep)
    if through:
        for t in through:
            if isinstance(x, t):
                return t(tdictify(v, through, deep=deep) for v in x)
    return x
