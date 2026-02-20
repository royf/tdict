import operator
from collections.abc import Iterable
from collections.abc import Mapping
from collections.abc import MutableMapping

__all__ = ['Bunch']


class Bunch(MutableMapping):
    """
    A `Mapping` with keys accessible either as attributes or as items.

    @DynamicAttrs
    """

    def __init__(self, /, *maps, **kwargs):
        """

        Args:
            *maps (Mapping): Update items from each map in order.
            **kwargs: Lastly, update items from `kwargs`.
        """
        super().__init__()
        for m in maps:
            type(self).update(self, m)
        type(self).update(self, kwargs)

    def __str__(self):
        """

        Returns:
            str: Informal string representation.
        """
        return f'{type(self).__name__}({", ".join(f"{k}={v}" for k, v in vars(self).items())})'

    def __repr__(self):
        """

        Returns:
            str: String representation.
        """
        return f'''{type(self).__name__}({", ".join(
            f"{k if isinstance(k, str) and k.isidentifier() else repr(k)}={v!r}" for k, v in vars(self).items())})'''

    def __getitem__(self, key):
        """

        Args:
            key (str): Item key.

        Returns:
            Item value.
        """
        return vars(self)[key]

    def __getattr__(self, key):
        return type(self).__getitem__(self, key)

    def __setitem__(self, key, val):
        """

        Args:
            key (str): Item key.
            val: Item value.
        """
        vars(self)[key] = val

    def __setattr__(self, key, val):
        return type(self).__setitem__(self, key, val)

    def __delitem__(self, key):
        """

        Args:
            key (str): Item key.
        """
        del vars(self)[key]

    def __len__(self):
        """

        Returns:
            int: Number of items.
        """
        return len(vars(self))

    def __iter__(self):
        """

        Returns:
            Iterator: Key iterator.
        """
        return iter(vars(self))

    def copy(self):
        return type(self)(self)

    def get_items(self, keys):
        """
        Get a `Bunch` mapping the `keys` to their values, or optionally default values if missing.
        If `keys` is a `Mapping`, it gives the default values, otherwise missing values are omitted.

        Args:
            keys (Mapping[str, Any] | Iterable[str]): Item keys, optionally mapping to their default values.

        Returns:
            Bunch: Mapping of `keys` to their values, optionally with default values if missing.
        """
        if isinstance(keys, Mapping):
            return Bunch({k: type(self).get(self, k, v) for k, v in keys.items()})
        else:
            return Bunch({k: type(self).__getitem__(self, k) for k in keys if k in self})

    def set_defaults(self, keys):
        """
        Set the value of any missing `keys`, then get a `Bunch` mapping all `keys` to their values.

        Args:
            keys (Mapping[str, Any]): Item keys, mapping to their default values.

        Returns:
            Bunch: Mapping of `keys` to their values, with set default values if missing.
        """
        return Bunch({k: type(self).setdefault(self, k, v) for k, v in keys.items()})

    def pop_items(self, keys):
        """
        Delete the items for `keys` and return them in a `Bunch`, optionally with default values if missing.
        If `keys` is a `Mapping`, it gives the default values, otherwise missing values are omitted.

        Args:
            keys (Mapping[str, Any] | Iterable[str]): Item keys, optionally mapping to their default values.

        Returns:
            Bunch: Mapping of `keys` to their popped values, optionally with default values if missing.
        """
        if isinstance(keys, Mapping):
            return Bunch({k: type(self).pop(self, k, v) for k, v in keys.items()})
        else:
            return Bunch({k: type(self).__delitem__(self, k) for k in keys if k in self})

    def __xor__(self, keys):
        """
        Get a copy with the items for `keys` deleted.

        Args:
            keys (Iterable[str]): Item keys.

        Returns:
            A `Bunch` with the same items except those in `keys`.
        """
        copy = type(self).copy(self)
        copy ^= keys
        return copy

    def __ixor__(self, keys):
        """
        Delete the items for `keys`.

        Args:
            keys (Iterable[str]): Item keys.
        """
        type(self).pop_items(self, keys)
        return self

    def merge(self, other, op):
        """
        Update items from `other`, applying the binary `op` to `(self[key], other[key])` for each `key` both contain.

        Args:
            other (Mapping[str, Any]): `Mapping` to merge from.
            op ((Any, Any) -> Any): Merge operator, applied as `op(self_val, other_val)`.

        Returns:
            Bunch: Updated `Mapping`.
        """
        for k, v in other.items():
            if k in self:
                self[k] = op(self[k], v)
            else:
                self[k] = v
        return self


class Op(object):
    def __init__(self, op, inplace):
        self.op = op
        self.inplace = inplace

    def __get__(self, obj, objtype=None):
        def apply(self_, other):
            if not self.inplace:
                self_ = type(self_).copy(self_)
            return type(self_).merge(self_, other, self.op)

        return apply.__get__(obj, objtype)


OPERATORS = {
    'add': operator.iadd,
    'floordiv': operator.ifloordiv,
    'or': lambda x, y: y,
    'lshift': operator.ilshift,
    'matmul': operator.imatmul,
    'mod': operator.imod,
    'mul': operator.imul,
    'pow': operator.ipow,
    'rshift': operator.irshift,
    'sub': operator.isub,
    'truediv': operator.itruediv,
}


def set_ops(cls_):
    for name, op in OPERATORS.items():
        setattr(cls_, f'__{name}__', Op(op, inplace=False))
        setattr(cls_, f'__i{name}__', Op(op, inplace=True))


set_ops(Bunch)
