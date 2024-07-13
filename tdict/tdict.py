import operator
from collections import abc


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
    >>> z = d.copy().with_deep(False)
    >>> assert list(z.items()) == list(d.items(deep=False))
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

    def __new__(cls, *maps, **attr):
        subcls = type(cls.__name__, (cls,), {
            '__new__': cls.new_with,
            '__reduce__': lambda self: (cls.init_with, (type(self).DEEP, type(self).DEFAULT), vars(self)),
        })
        return super().__new__(subcls)  # type: ignore

    def __init__(self, *maps, **attr):
        """

        Args:
            *maps (Mapping): Update attributes from these `Mapping`s.
                             Values that are themselves `Mapping`s are deep-copied as sub-`Tdict`s.
            **attr: Extra attributes.
        """
        super().__init__()
        for m in maps:
            shallow_map = vars(m) if isinstance(m, Tdict) else m
            for k, v in shallow_map.items():
                if isinstance(v, abc.Mapping):
                    item = vars(self).setdefault(k, type(self)())
                    type(item).update(item, v)
                else:
                    vars(self)[k] = v
        type(self).update(self, attr)

    DEEP = True
    DEFAULT = None

    @classmethod
    def new_with(cls, cls_, *args, **kwargs):
        d = cls.__new__(cls).with_deep(cls_.DEEP).with_default(cls_.DEFAULT)
        cls.__init__(d, *args, **kwargs)
        return d

    @classmethod
    def init_with(cls, deep, default):
        return cls().with_deep(deep).with_default(default)

    def __getitem__(self, k, def_default=True, default=None):
        """

        Args:
            k (str | tuple): Item key. May be a `tuple` for deep access. Creates nested `Tdict`s if needed for default.
            def_default (bool, optional): `True` for `self`'s default, `False` for the arg default, None for neither.
            default: Default value to set and get if `cls_default` is `False`.

        Returns:
            Item value.

        Raises:
            KeyError: Key path is missing and no default exists.
        """
        try:
            if isinstance(k, tuple):
                if len(k) == 0:
                    return self
                elif len(k) == 1:
                    return type(self).__getitem__(self, k[0], def_default, default)
                elif k[0] not in vars(self):
                    if def_default is None:
                        raise KeyError(k[0])
                    else:
                        d = type(self)()
                        vars(self)[k[0]] = d
                        return type(d).__getitem__(d, k[1:], def_default, default)
                else:
                    d = vars(self)[k[0]]
                    if isinstance(d, Tdict):
                        return type(d).__getitem__(d, k[1:], def_default, default)
                    else:
                        raise KeyError(k[0])
            elif k not in vars(self):
                if def_default is None:
                    raise KeyError(k)
                elif def_default:
                    v = type(self).DEFAULT()
                else:
                    v = default
                vars(self)[k] = v
                return v
            else:
                return vars(self)[k]
        except KeyError:
            raise KeyError(k) from None

    def __setitem__(self, k, v):
        """

        Args:
            k (str | tuple): Item key. May be a `tuple` for deep access, which creates nested `Tdict`s as needed.
            v: Item value.

        Raises:
            KeyError: Item key is an empty `tuple` or its path is blocked by a non-`Tdict`.
        """
        try:
            if isinstance(k, tuple):
                if len(k) == 0:
                    raise KeyError("cannot assign to root")
                elif len(k) == 1:
                    vars(self)[k[0]] = v
                elif k[0] not in vars(self):
                    d = type(self)()
                    vars(self)[k[0]] = d
                    d[k[1:]] = v
                else:
                    d = vars(self)[k[0]]
                    if isinstance(d, Tdict):
                        d[k[1:]] = v
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
            k (str | tuple): Item key. May be a `tuple` for deep access.

        Raises:
            KeyError: Item key is an empty `tuple` or its path is missing.
        """
        try:
            if isinstance(k, tuple):
                if len(k) == 0:
                    raise KeyError("cannot delete root")
                elif len(k) == 1:
                    del vars(self)[k[0]]
                elif k[0] in vars(self):
                    d = vars(self)[k[0]]
                    if isinstance(d, Tdict):
                        del d[k[1:]]
                    else:
                        raise KeyError(k)
                else:
                    raise KeyError(k[0])
            else:
                del vars(self)[k]
        except KeyError:
            raise KeyError(k) from None

    def access_default(self, get=True, k=None, default=None, /, **kwargs):
        """

        Args:
            get (bool): Whether to also set default or just get it.
            k (str | tuple): Item key. May be a `tuple` for deep access.
            default: Item value to get if missing.
            **kwargs: If `k` and `default` are `None`, a single item used for `{k: default}`.

        Raises:
            ValueError: Multiple keys provided.
        """
        try:
            if len(kwargs) == 1 and k is None and default is None:
                k, default = next(iter(kwargs.items()))
            elif len(kwargs) > 1:
                raise ValueError("get takes a single key")
            return type(self).__getitem__(self, k, use_default=None if get else 'arg', default=default)
        except KeyError:
            return default

    def get(self, k=None, default=None, /, **kwargs):
        """

        Args:
            k (str | tuple): Item key. May be a `tuple` for deep access.
            default: Item value to get if missing.
            **kwargs: If `k` and `default` are `None`, a single item used for `{k: default}`.

        Raises:
            ValueError: Multiple keys provided.
        """
        return self.access_default(True, k, default, **kwargs)

    def setdefault(self, k=None, default=None, /, **kwargs):
        """

        Args:
            k (str | tuple): Item key. May be a `tuple` for deep access, which creates nested `Tdict`s as needed.
            default: Item value to set and get if missing.
            **kwargs: If `k` and `default` are `None`, a single item used for `{k: default}`.

        Raises:
            ValueError: Multiple keys provided.
        """
        return self.access_default(False, k, default, **kwargs)

    def as_dict(self):
        """

        Returns:
            dict: The object's dict.
        """
        return vars(self)

    def with_deep(self, deep=True):
        """

        Args:
            deep (bool): Whether to iterate recursively by default.

        Returns:
            Tdict: Sets deep and returns self.
        """
        type(self).DEEP = deep
        return self

    def with_shallow(self, deep=False):
        """

        Args:
            deep (bool): Whether to iterate recursively by default.

        Returns:
            Tdict: Sets deep and returns self.
        """
        type(self).DEEP = deep
        return self

    def with_default(self, default=None):
        """

        Args:
            default (abc.Callable): Callable that returns a value to be set when getting a missing item.

        Returns:
            Tdict: Sets the default factory and returns self.
        """
        type(self).DEFAULT = default
        return self

    def keys(self, deep=None):
        """

        Args:
            deep (bool, optional): Whether to iterate recursively. Default: `self`'s default if set, `True` if not.

        Yields:
            Next key.
        """
        return tdict_keys(self, deep)

    def values(self, deep=None):
        """

        Args:
            deep (bool, optional): Whether to iterate recursively. Default: `self`'s default if set, `True` if not.

        Yields:
            Next value.
        """
        return tdict_values(self, deep)

    def items(self, deep=None):
        """

        Args:
            deep (bool, optional): Whether to iterate recursively. Default: `self`'s default if set, `True` if not.

        Yields:
            Next item.
        """
        return tdict_items(self, deep)

    def __iter__(self):
        """

        Yields:
            Next key.
        """
        return type(self).keys(self)

    def __len__(self):
        """

        Returns:
            int: Number of items, or of leaf (non-`Tdict`) values if iterating recursively.
        """
        return sum(1 for _ in type(self).values(self))

    def __repr__(self):
        """

        Returns:
            str: String representation of `self`.
        """
        return f'{type(self).__name__}({", ".join(
            f"{k if isinstance(k, str) and k.isidentifier() else repr(str(k))}={v!r}" for k, v in vars(self).items())})'

    def __contains__(self, k):
        """

        Args:
            k (str | tuple): Item key. `tuple` for deep access or `str` for shallow.

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

    def copy(self, deep=True, exclude=None):
        """

        Args:
            deep (bool, optional): Whether to copy recursively. Unlike `copy.deepcopy`, only goes through `Tdict`s.
            exclude (abc.Iterable): Iterable of keys to exclude. Default: no keys excluded.

        Returns:
            Tdict: Copy of `self`.
        """
        res = type(self)()
        if deep or (deep is None and type(self).DEEP):
            for k, v in vars(self).items():
                if exclude is not None and (k,) in exclude:
                    continue
                if isinstance(v, Tdict):
                    if exclude is None:
                        excl = None
                    else:
                        excl = (k__ for k_, *k__ in exclude if k is k_ or k == k_)
                    vars(res)[k] = type(v).copy(v, deep, excl)
                else:
                    vars(res)[k] = v
        else:
            for k, v in vars(self).items():
                if exclude is not None and k in exclude:
                    continue
                vars(res)[k] = v
        return res

    def __xor__(self, other):
        """
        Shorthand for `self.copy(deep=False, exclude=other)`.

        Returns:
            Tdict: Copy of `self` with shallow keys in `other` excluded.
        """
        return type(self).copy(self, False, other)

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
                            type(v_).update(v_, v, o)
                        else:
                            vars(self)[k] = v
                    elif o is None:
                        vars(self)[k] = type(self).ensure_tdict(v)
                    else:
                        vars(self)[k] = o(v_, v)
                else:
                    vars(self)[k] = type(self).ensure_tdict(v)
        else:
            for k, v in vars(self).items():
                if isinstance(v, Tdict):
                    type(v).update(v, d, o)
                elif o is None:
                    vars(self)[k] = d
                else:
                    vars(self)[k] = o(v, d)
        return self

    @classmethod
    def ensure_tdict(cls, d):
        """

        Args:
            d: possible mapping to ensure is a `Tdict`.

        Returns:
            Tdict: A newly constructed `Tdict` if a mapping d isn't one already, otherwise d itself.
        """
        if isinstance(d, abc.Mapping) and not isinstance(d, Tdict):
            return cls(d)
        else:
            return d


def tdict_keys(d, deep=None):
    if deep or (deep is None and type(d).DEEP):
        for k, v in vars(d).items():
            if isinstance(v, Tdict):
                for k_ in type(v).keys(v, deep):
                    yield k, *k_
            else:
                yield k,
    else:
        yield from vars(d).keys()


def tdict_values(d, deep=None):
    if deep or (deep is None and type(d).DEEP):
        for v in vars(d).values():
            if isinstance(v, Tdict):
                yield from type(v).values(v, deep)
            else:
                yield v
    else:
        yield from vars(d).values()


def tdict_items(d, deep=None):
    if deep or (deep is None and type(d).DEEP):
        for k, v in vars(d).items():
            if isinstance(v, Tdict):
                for k_, v_ in type(v).items(v, deep):
                    yield (k, *k_), v_
            else:
                yield (k,), v
    else:
        yield from vars(d).items()


class _Op(object):
    def __init__(self, o, inplace=True):
        self.o = o
        self.inplace = inplace

    def __get__(self, obj, objtype=None):
        def apply(x, y):
            if not self.inplace:
                x = type(x).copy(x, deep=True)
            return type(x).update(x, y, self.o)

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


def set_ops(cls):
    for name, op in _OPERATORS.items():
        setattr(cls, f'__{name}__', _Op(op, inplace=False))
        setattr(cls, f'__i{name}__', _Op(op, inplace=True))


set_ops(Tdict)


def tdictify(x, through=None, deep=True, default=None):
    """
    Return a recursively `Tdict`ified version of `x`:
        If `x` is a `Mapping`, return a `Tdict` with the same keys and `Tdict`ified values.
        If `x` is an instance of a type in `through`, return a new instance of that type with `Tdict`ified elements.
        Otherwise, return `x`.

    Args:
        x: The object to `Tdict`ify.
        through (Sequence[Type]): list of types through which to deep-copy and `Tdict`ify; e.g., `[list, tuple]`.
        deep (bool): whether the constructed Tdict iterates keys, values, and items recursively by default.
        default: default value to set and return, when getting a missing key.

    Returns:
        Tdict: `Tdict`ified version of `x`.
    """
    if isinstance(x, abc.Mapping):
        shallow_map = vars(x) if isinstance(x, Tdict) else x
        d = Tdict({k: tdictify(v, through, deep, default) for k, v in shallow_map.items()})
        return type(d).with_default(type(d).with_deep(d, deep), default)
    if through:
        for t in through:
            if isinstance(x, t):
                return t(tdictify(v, through, deep, default) for v in x)
    return x
