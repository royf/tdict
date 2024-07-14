import operator
from collections import abc
from typing import Iterable
from typing import Mapping


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
        d = cls.__new__(cls)
        cls.__init__(d.with_deep(cls_.DEEP).with_default(cls_.DEFAULT), *args, **kwargs)  # type: ignore
        return d

    @classmethod
    def init_with(cls, deep, default):
        return cls().with_deep(deep).with_default(default)

    def __getitem__(self, k, self_default=True, default=None):
        """

        Args:
            k (str | tuple): Item key. May be a `tuple` for deep access. Creates nested `Tdict`s if needed for default.
            self_default (bool): `True` for `self`'s default, `Ellipsis` for the arg default, `False` for neither.
            default: Default value to set and get if `self_default` is `Ellipsis`.

        Returns:
            Item value.

        Raises:
            KeyError: Key path is missing and no default exists.
        """
        if self_default is True:
            use_default = type(self).DEFAULT is not None
        else:
            use_default = self_default is ...
        try:
            if isinstance(k, tuple):
                if len(k) == 0:
                    return self
                elif len(k) == 1:
                    return type(self).__getitem__(self, k[0], self_default, default)
                elif k[0] not in vars(self):
                    if use_default:
                        d = type(self)()
                        vars(self)[k[0]] = d
                        return type(d).__getitem__(d, k[1:], self_default, default)
                    else:
                        raise KeyError(k[0])
                else:
                    d = vars(self)[k[0]]
                    if isinstance(d, Tdict):
                        return type(d).__getitem__(d, k[1:], self_default, default)
                    else:
                        raise KeyError(k[0])
            elif k not in vars(self):
                if use_default:
                    if self_default is True:
                        v = type(self).DEFAULT()
                    else:
                        v = default
                    vars(self)[k] = v
                    return v
                else:
                    raise KeyError(k)
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

    def access_default(self, key=None, default=None, get_default=None, set_default=False, /, **kwargs):
        """
        Get all the values for keys in `key` and `kwargs`, or defaults if missing.
        If `key` is a single key (`str` or `tuple` for deep access) and no `kwargs` are given,
            then `default` is returned if its value is missing.
        If `key` is multiple keys (`set` or `Mapping`), then a `Tdict` is returned.
            If `get_default` is `False`, missing values are omitted from the `Tdict` (which could make it size 0 or 1).
            Otherwise, defaults are taken from the default values given in `key`, or as `default` if `key` is a `set`.
        If `set_default` is `True`, default values are also set in `self`, so none end up missing.
            For `tuple` keys, `Tdict` paths are created as needed to set the default values.

        Args:
            key (str | tuple | set | Mapping): Item key(s). Can be a `Mapping` of keys to their defaults.
            default: Default value for missing key(s). Default: None for single key, omit missing of multiple keys.
                Ignored if `k` is a `Mapping` providing each key's default.
            get_default (bool, optional): Whether to return missing keys with default values.
                Default: `True` if `default` is not `None`.
            set_default (bool): Whether to also set default values for missing keys.
            **kwargs: additional keys and their defaults.

        Returns:
            The value (or `default`) of a single `key`, or `Tdict` with values of multiple keys.
        """
        single_key = False
        if key is None:
            key = {}
        elif isinstance(key, set):
            key = {k: default for k in key}
        elif not isinstance(key, abc.Mapping):
            key = {key: default}
            if len(kwargs) == 0:
                single_key = True
        key.update(kwargs)
        if get_default is None:
            get_default = default is not None
        res = Tdict()
        for k, d in key.items():
            self_default = ... if set_default else False
            try:
                res[k] = type(self).__getitem__(self, k, self_default, d)
            except KeyError:
                if get_default or single_key:
                    res[k] = d
        if single_key:
            return next(iter(res.values()))
        else:
            return res

    def get(self, key=None, default=None, get_default=None, /, **kwargs):
        """
        Get all the values for keys in `key` and `kwargs`, or defaults if missing.
        If `key` is a single key (`str` or `tuple` for deep access) and no `kwargs` are given,
            then `default` is returned if its value is missing.
        If `key` is multiple keys (`set` or `Mapping`), then a `Tdict` is returned.
            If `get_default` is `False`, missing values are omitted from the `Tdict` (which could make it size 0 or 1).
            Otherwise, defaults are taken from the default values given in `key`, or as `default` if `key` is a `set`.

        Args:
            key (str | tuple | set | Mapping): Item key(s). Can be a `Mapping` of keys to their defaults.
            default: Default value for missing key(s). Default: None for single key, omit missing of multiple keys.
                Ignored if `k` is a `Mapping` providing each key's default.
            get_default (bool, optional): Whether to return missing keys with default values.
            **kwargs: additional keys and their defaults.

        Returns:
            The value (or `default`) of a single `key`, or `Tdict` with values of multiple keys.
        """
        return self.access_default(key, default, get_default, **kwargs)

    def setdefault(self, key=None, default=None, /, **kwargs):
        """
        Get all the values for keys in `key` and `kwargs`, or defaults if missing.
        If `key` is a single key (`str` or `tuple` for deep access) and no `kwargs` are given,
            then `default` is returned if its value is missing.
        If `key` is multiple keys (`set` or `Mapping`), then a `Tdict` is returned.
            Defaults are taken from the default values given in `key`, or as `default` if `key` is a `set`.
        Missing keys also have their default values set in `self`.
            For `tuple` keys, `Tdict` paths are created as needed to set the default values.

        Args:
            key (str | tuple | set | Mapping): Item key(s). Can be a `Mapping` of keys to their defaults.
            default: Default value for missing key(s). Default: None.
                Ignored if `k` is a `Mapping` providing each key's default.
            **kwargs: additional keys and their defaults.

        Returns:
            The value (or `default`) of a single `key`, or `Tdict` with values of multiple keys.
        """
        return self.access_default(key, default, None, True, **kwargs)

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
            exclude (Iterable): Iterable of keys to exclude. Default: no keys excluded.

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
        through (Iterable): list of types through which to deep-copy and `Tdict`ify; e.g., `[list, tuple]`.
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
