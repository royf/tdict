import functools
import operator
from collections import abc
from typing import Iterable
from typing import Mapping

CANARY_ATTRS = {'_ipython_canary_method_should_not_exist_'}


class Tdict(abc.MutableMapping):
    """
    Tree dict.

    Values of `str` keys can be accessed either as attributes or as items.
    Values of `tuple` keys are stored in nested `Tdict`s.

    @DynamicAttrs
    """

    def __new__(cls, /, *map_trees, **map_tree):
        subcls = type(cls.__name__, (cls,), {
            '__new__': cls.new_with,
            '__reduce__': lambda self: (cls.init_with, (type(self).DEEP, type(self).DEFAULT_FACTORY), vars(self)),
        })
        return super().__new__(subcls)  # type: ignore

    def __init__(self, /, *map_trees, **map_tree):
        """

        Args:
            *map_trees (Mapping): Update attributes from copies of these `Mapping` trees.
            **map_tree: An additional `Mapping` tree given as kwargs.
        """
        super().__init__()
        for m in map_trees:
            type(self).update(self, m)
        type(self).update(self, map_tree)

    DEEP = True
    DEFAULT_FACTORY = None

    @classmethod
    def new_with(cls, cls_, /, *args, **kwargs):
        d = cls.__new__(cls)
        cls.__init__(d.set_deep(cls_.DEEP).set_default_factory(cls_.DEFAULT_FACTORY), *args, **kwargs)  # type: ignore
        return d

    @classmethod
    def init_with(cls, deep, default_factory):
        return cls().set_deep(deep).set_default_factory(default_factory)

    def set_deep(self, deep=True):
        """

        Args:
            deep (bool or optional): Whether to iterate recursively by default.

        Returns:
            Tdict: Sets DEEP and returns self.
        """
        type(self).DEEP = deep
        return self

    def set_shallow(self, deep=False):
        """

        Args:
            deep (bool or optional): Whether to iterate recursively by default.

        Returns:
            Tdict: Sets DEEP and returns self.
        """
        type(self).DEEP = deep
        return self

    def set_default_factory(self, default_factory):
        """

        Args:
            default_factory (abc.Callable): Callable that returns a value to be set when getting a missing item.

        Returns:
            Tdict: Sets DEFAULT_FACTORY and returns self.
        """
        type(self).DEFAULT_FACTORY = default_factory
        return self

    def __str__(self):
        """

        Returns:
            str: Informal string representation of `self`.
        """
        return f'{type(self).__name__}({", ".join(f"{k}={v}" for k, v in vars(self).items())})'

    def __repr__(self):
        """

        Returns:
            str: String representation of `self`.
        """
        return f'''{type(self).__name__}({", ".join(
            f"{k if isinstance(k, str) and k.isidentifier() else repr(k)}={v!r}" for k, v in vars(self).items())})'''

    def __getitem__(self, key, self_default=True, default=None):
        """

        Args:
            key (str or tuple): Item key. May be a `tuple` for deep access.
                Creates nested `Tdict`s if needed for default.
            self_default (bool or optional): `True` uses the default factory, `Ellipsis` uses `default`,
                `False` uses neither.
            default (optional): Default value to set and get if `self_default` is `Ellipsis`.

        Returns:
            Item value.

        Raises:
            KeyError: Key path is missing and no default is used.
        """
        try:
            d = self
            if isinstance(key, tuple):
                if len(key) == 0:
                    return self
                for k in key[:-1]:
                    if k in vars(d):
                        d = vars(d)[k]
                        if not isinstance(d, Tdict):
                            raise KeyError(k)
                    elif (self_default is True and type(d).DEFAULT_FACTORY is not None) or self_default is ...:
                        d_ = type(d)()
                        vars(d)[k] = d_
                        d = d_
                    else:
                        raise KeyError(k)
                key = key[-1]
            if key in vars(d):
                return vars(d)[key]
            elif self_default is True and type(d).DEFAULT_FACTORY is not None:
                v = type(d).DEFAULT_FACTORY()
            elif self_default is ...:
                v = default
            else:
                raise KeyError(key)
            vars(d)[key] = v
            return v
        except KeyError:
            raise KeyError(key) from None

    def __getattr__(self, key):
        if key in CANARY_ATTRS:
            return True
        else:
            return type(self).__getitem__(self, key)

    def __setitem__(self, key, val):
        """

        Args:
            key (str or tuple): Item key. May be a `tuple` for deep access, which creates nested `Tdict`s as needed.
            val: Item value.

        Raises:
            KeyError: Item key is an empty `tuple` or its path is blocked by a non-`Tdict`.
        """
        try:
            d = self
            if isinstance(key, tuple):
                if len(key) == 0:
                    raise KeyError("cannot assign to root")
                for k in key[:-1]:
                    if k in vars(d):
                        d = vars(d)[k]
                        if not isinstance(d, Tdict):
                            raise KeyError(k)
                    else:
                        d_ = type(d)()
                        vars(d)[k] = d_
                        d = d_
                key = key[-1]
            vars(d)[key] = val
        except KeyError:
            raise KeyError(key) from None

    __setattr__ = __setitem__

    def __delitem__(self, key):
        """

        Args:
            key (str or tuple): Item key. May be a `tuple` for deep access.

        Raises:
            KeyError: Item key is an empty `tuple` or its path is missing.
        """
        try:
            d = self
            if isinstance(key, tuple):
                if len(key) == 0:
                    raise KeyError("cannot delete root")
                for k in key[:-1]:
                    if k in vars(d):
                        d = vars(d)[k]
                        if not isinstance(d, Tdict):
                            raise KeyError(k)
                    else:
                        raise KeyError(k)
                key = key[-1]
            del vars(d)[key]
        except KeyError:
            raise KeyError(key) from None

    def __contains__(self, key):
        """

        Args:
            key (str or tuple): Item key. May be `tuple` for deep access.

        Returns:
            bool: Key existence.
        """
        d = self
        if isinstance(key, tuple):
            if len(key) == 0:
                return True
            for k in key[:-1]:
                if k in vars(d):
                    d = vars(self)[k]
                    if not isinstance(d, Tdict):
                        raise False
                else:
                    return False
            key = key[-1]
        return key in vars(d)

    def access_default(self, key=None, default=None, get_default=None, set_default=False, del_keys=False, /, **keys):
        """
        Get all the values for keys in `key` and `keys`, or defaults if missing.
        If a single key (`str` or `tuple` for deep access) is given across `key` and `keys`,
            then its `default` is returned if its value is missing.
        If multiple keys (`Sequence` other than `tuple`, or `Mapping`) or no keys are given, then a `Tdict` is returned.
            If `get_default` is `False`, missing values are omitted from the `Tdict` (which could make its size 0 or 1).
            Otherwise, defaults are `default` if `key` is a `Sequence`, else the `Mapping` values.
            `get_default` defaults (`None`) to omitting only missing values whose default is `None`.
        If `set_default` is `True`, any returned (but not omitted) default values are also set.
            For `tuple` keys, `Tdict` paths are created as needed to set the default values.
        If `del_keys` is `True`, any existing keys are deleted.

        Args:
            key (str or tuple or Sequence or Mapping or optional): Item key(s), optionally mapping to their defaults.
            default (optional): Default value for missing key(s).
                Default: `None` for single key, omit missing of multiple keys.
                Ignored if `key` is a `Mapping` providing each key's default.
            get_default (bool or optional): Whether to return missing keys with default values.
                Default (`None`): omit only missing values whose default is `None`.
            set_default (bool or optional): Whether to also set default values for returned missing keys.
            del_keys (bool or optional): Whether to also delete the keys (supersedes `set_default`).
            **keys: additional keys and their defaults.

        Returns:
            The value (or `default`) of a single `key`, or `Tdict` with values of multiple keys.
        """
        single_key = False
        if key is None:
            key = {}
            single_key = len(keys) == 1
        elif isinstance(key, (abc.Sequence, abc.Set)) and not isinstance(key, tuple):
            key = {k: default for k in key}
        elif not isinstance(key, abc.Mapping):
            key = {key: default}
            single_key = len(keys) == 0
        key.update(keys)
        res = type(self)()
        for k, d in key.items():
            self_default = ... if (set_default and not del_keys) else False
            try:
                res[k] = type(self).__getitem__(self, k, self_default, d)
            except KeyError:
                if get_default is True or (get_default is None and d is not None) or single_key:
                    res[k] = d
            else:
                if del_keys:
                    type(self).__delitem__(self, k)
        if single_key:
            return next(iter(vars(res).values()))
        else:
            return res

    def get(self, key=None, default=None, get_default=None, /, **keys):
        """
        Get all the values for keys in `key` and `keys`, or defaults if missing.
        If a single key (`str` or `tuple` for deep access) is given across `key` and `keys`,
            then its `default` is returned if its value is missing.
        If multiple keys (`Sequence` other than `tuple`, or `Mapping`) or no keys are given, then a `Tdict` is returned.
            If `get_default` is `False`, missing values are omitted from the `Tdict` (which could make its size 0 or 1).
            Otherwise, defaults are `default` if `key` is a `Sequence`, else the `Mapping` values.
            `get_default` defaults (`None`) to only omitting missing values whose default is `None`.

        Args:
            key (str or tuple or Sequence or Mapping or optional): Item key(s), optionally mapping to their defaults.
            default (optional): Default value for missing key(s).
                Default: `None` for single key, omit missing of multiple keys.
                Ignored if `key` is a `Mapping` providing each key's default.
            get_default (bool or optional): Whether to return missing keys with default values.
                Default (`None`): omit only missing values whose default is `None`.
            **keys: additional keys and their defaults.

        Returns:
            The value (or `default`) of a single `key`, or `Tdict` with values of multiple keys.
        """
        return self.access_default(key, default, get_default, **keys)

    def getdefault(self, key=None, default=None, /, **keys):
        """
        Get all the values for keys in `key` and `keys`, or defaults if missing.
        If a single key (`str` or `tuple` for deep access) is given across `key` and `keys`,
            then `default` is returned if its value is missing.
        If multiple keys (`Sequence` other than `tuple`, or `Mapping`) or no keys are given, then a `Tdict` is returned.
            Defaults are `default` if `key` is a `Sequence`, else the `Mapping` values.

        Args:
            key (str or tuple or Sequence or Mapping or optional): Item key(s), optionally mapping to their defaults.
            default (optional): Default value for missing key(s).
                Default: `None` for single key, omit missing of multiple keys.
                Ignored if `key` is a `Mapping` providing each key's default.
            **keys: additional keys and their defaults.

        Returns:
            The value (or `default`) of a single `key`, or `Tdict` with values of multiple keys.
        """
        return self.access_default(key, default, True, **keys)

    def setdefault(self, key=None, default=None, /, **keys):
        """
        Get all the values for keys in `key` and `keys`, or defaults if missing.
        If a single key (`str` or `tuple` for deep access) is given across `key` and `keys`,
            then `default` is returned if its value is missing.
        If multiple keys (`Sequence` other than `tuple`, or `Mapping`) or no keys are given, then a `Tdict` is returned.
            Defaults are `default` if `key` is a `Sequence`, else the `Mapping` values.
        Missing keys also have their default values set in `self`.
            For `tuple` keys, `Tdict` paths are created as needed to set the default values.

        Args:
            key (str or tuple or Sequence or Mapping or optional): Item key(s), optionally mapping to their defaults.
            default (optional): Default value for missing key(s).
                Default: `None` for single key, omit missing of multiple keys.
                Ignored if `key` is a `Mapping` providing each key's default.
            **keys: additional keys and their defaults.

        Returns:
            The value (or `default`) of a single `key`, or `Tdict` with values of multiple keys.
        """
        return self.access_default(key, default, True, True, **keys)

    def pop(self, key=None, default=None, get_default=None, /, **keys):
        """
        Pop all the keys in `key` and `keys` and return their values, or defaults if missing.
        If a single key (`str` or `tuple` for deep access) is given across `key` and `keys`,
            then `default` is returned if its value is missing.
        If multiple keys (`Sequence` other than `tuple`, or `Mapping`) or no keys are given, then a `Tdict` is returned.
            If `get_default` is `False`, missing values are omitted from the `Tdict` (which could make its size 0 or 1).
            Otherwise, defaults are `default` if `key` is a `Sequence`, else the `Mapping` values.
            `get_default` defaults (`None`) to omitting only missing values whose default is `None`.

        Args:
            key (str or tuple or Sequence or Mapping or optional): Item key(s), optionally mapping to their defaults.
            default(optional): Default value for missing key(s).
                Default: `None` for single key, omit missing of multiple keys.
                Ignored if `key` is a `Mapping` providing each key's default.
            get_default (bool or optional): Whether to return missing keys with default values.
                Default (`None`): omit only missing values whose default is `None`.
            **keys: additional keys and their defaults.

        Returns:
            The value (or `default`) of a single `key`, or `Tdict` with values of multiple keys.
        """
        return self.access_default(key, default, True, False, True, **keys)

    def keys(self, deep=None):
        """

        Args:
            deep (bool or optional): Whether to iterate recursively. Default: `self`'s DEEP.

        Yields:
            Next key.
        """
        return tdict_keys(self, deep)

    def values(self, deep=None):
        """

        Args:
            deep (bool or optional): Whether to iterate recursively. Default: `self`'s DEEP.

        Yields:
            Next value.
        """
        return tdict_values(self, deep)

    def items(self, deep=None):
        """

        Args:
            deep (bool or optional): Whether to iterate recursively. Default: `self`'s DEEP.

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
            int: Number of `Tdict` tree (shallow-, deep-, or mixed-access) values (with repetition).
        """
        return sum(1 for _ in type(self).values(self))

    def as_dict(self):
        """

        Returns:
            dict: The object's `dict`.
        """
        return vars(self)

    @classmethod
    def cast(cls, map_tree, through=None, op=None):
        """

        Args:
            map_tree: `Mapping` tree to cast as `Tdict` tree.
            through (Iterable or optional): list of types through which to recurse; e.g., `[list, tuple]`.
            op (Any -> Any or optional): conversion operator.

        Returns:
            Tdict: A `Tdict` tree copy of the `Mapping` tree, with each leaf processed by `op`.
        """
        if isinstance(map_tree, abc.Mapping):
            if isinstance(map_tree, Tdict):
                res = type(map_tree)()
                items = map_tree.items(deep=False)
            else:
                res = cls()
                items = map_tree.items()
            for k, v in items:
                vars(res)[k] = cls.cast(v, op)
            return res
        if through:
            for t in through:
                if isinstance(map_tree, t):
                    return t(cls.cast(v, through, op) for v in map_tree)
        if op is None:
            return map_tree
        return op(map_tree)

    def copy(self, deep=None, exclude=None):
        """

        Args:
            deep (bool or optional): Whether to copy recursively.
                Unlike `copy.deepcopy`, only goes through `Tdict` nodes.
                Default: respects each node's DEEP attribute.
            exclude (Iterable or optional): `Iterable` of keys to exclude.
                Default: no keys excluded.

        Returns:
            Tdict: Copy of `self`.
        """
        if exclude is not None:
            exclude = set(ex if isinstance(ex, tuple) else (ex,) for ex in exclude)
        res = type(self)()
        if deep or (deep is None and type(self).DEEP):
            for k, v in vars(self).items():
                if exclude is not None and (k,) in exclude:
                    continue
                if isinstance(v, Tdict):
                    if exclude is None:
                        sub_exclude = None
                    else:
                        sub_exclude = set(ex[1:] for ex in exclude if ex[0] == k)
                    vars(res)[k] = type(v).copy(v, deep, sub_exclude)
                else:
                    vars(res)[k] = v
        else:
            for k, v in vars(self).items():
                if exclude is not None and (k,) in exclude:
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

    def __ixor__(self, other):
        """
        Shorthand for `self.pop(other)`.
        """
        type(self).pop(self, other)

    def update(self, other, op=None):
        """
        Update `self` from another `Mapping` tree, with the following logic.
        In inner nodes that `self` and `other` share, for each key in `other`:
            - If it is missing in `self`, add that item as a `Tdict` tree copy of the `Mapping` subtree.
            - If it is a leaf (non-`Tdict`) in `self`:
                - The default `op` replaces that item with a `Tdict` tree copy of the `Mapping` subtree.
                - Any other `op` is applied to the leaf in `self` and each leaf under `other`, replacing the latter.
            - If it is a `Tdict` in `self` and a leaf (non-`Mapping`) in `other`:
                - The default `op` replaces the `self` `Tdict` subtree with the leaf value in `other`.
                - Any other `op` is applied to each leaf under `self` and the `other` value, replacing the former.
            - Inner nodes in both `self` and `other` are recursed over.
        Note that `other` must be a `Mapping` when `op` is `None`, because the root of `self` cannot be replaced.
        The overall result with the default `op` has:
            - All leafs in `other`, and any leaf in `self` that neither prefixes, nor is prefixed by, a leaf in `other`.
            - The leaf values in `other` of the former and in `self` of the latter.
        The overall result with any other `op` has:
            - Any leaf key in `self` or `other` that isn't a proper prefix of another leaf key in either source.
            - The original values of leafs in either source that don't have a proper prefix leaf in the other source.
            - Otherwise, the value is `op(self_val, other_val)`,
                with the operands taking the leaf value in one source and the prefix value in the other source.

        Args:
            other: Update from a `Mapping` tree.
            op ((Any, Any) -> Any): Update operator, applied as `op(self_val, other_val)`.
                Default (`None`) has a special behavior described in the docstring.

        Returns:
            Tdict: `self` after update.
        """
        if isinstance(other, abc.Mapping):
            try:
                items = other.items(deep=False)  # type: ignore
            except TypeError:
                items = other.items()
            for k, other_val in items:
                if k in vars(self):
                    self_val = vars(self)[k]
                    if isinstance(self_val, Tdict):
                        if isinstance(other_val, abc.Mapping) or op is not None:
                            type(self_val).update(self_val, other_val, op)
                        else:
                            vars(self)[k] = other_val
                    else:
                        cast_op = None if op is None else functools.partial(op, self_val)
                        vars(self)[k] = type(self).cast(other_val, cast_op)
                else:
                    vars(self)[k] = type(self).cast(other_val)
        elif op is None:
            raise ValueError("cannot update root")
        else:
            for k, v in vars(self).items():
                if isinstance(v, Tdict):
                    type(v).update(v, other, op)
                else:
                    vars(self)[k] = op(v, other)
        return self


# TODO: make these dict views
def tdict_keys(d, deep=None):
    if deep or (deep is None and type(d).DEEP):
        for k, v in vars(d).items():
            if isinstance(v, Tdict):
                for k_ in type(v).keys(v, deep):
                    if deep or (deep is None and type(v).DEEP):
                        yield k, *k_
                    else:
                        yield k, k_
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
                    if deep or (deep is None and type(v).DEEP):
                        yield (k, *k_), v_
                    else:
                        yield (k, k_), v_
            else:
                yield (k,), v
    else:
        yield from vars(d).items()


class Op(object):
    def __init__(self, op, inplace=True):
        self.op = op
        self.inplace = inplace

    def __get__(self, obj, objtype=None):
        def apply(self_, other):
            if not self.inplace:
                self_ = type(self_).copy(self_)
            return type(self_).update(self_, other, self.op)

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


def set_ops(cls_):
    for name, op in OPERATORS.items():
        setattr(cls_, f'__{name}__', Op(op, inplace=False))
        setattr(cls_, f'__i{name}__', Op(op, inplace=True))


set_ops(Tdict)
