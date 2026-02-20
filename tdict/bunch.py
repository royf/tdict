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
        super().__setattr__('d', {})
        for m in maps:
            self.d.update(m)
        self.d.update(kwargs)

    def __str__(self):
        """

        Returns:
            str: Informal string representation.
        """
        return f'{type(self).__name__}({", ".join(f"{k}={v}" for k, v in self.d.items())})'

    def __repr__(self):
        """

        Returns:
            str: String representation.
        """
        return f'''{type(self).__name__}({", ".join(
            f"{k if isinstance(k, str) and k.isidentifier() else repr(k)}={v!r}" for k, v in self.d.items())})'''

    def __getitem__(self, key):
        """

        Args:
            key (str): Item key.

        Returns:
            Item value.
        """
        return self.d[key]

    def __getattr__(self, key):
        try:
            return self.d[key]
        except KeyError:
            raise AttributeError(key) from None

    def __setitem__(self, key, val):
        """

        Args:
            key (str): Item key.
            val: Item value.
        """
        self.d[key] = val

    def __setattr__(self, key, val):
        self.d[key] = val

    def __delitem__(self, key):
        """

        Args:
            key (str): Item key.
        """
        del self.d[key]

    def __delattr__(self, key):
        del self.d[key]

    def __len__(self):
        """

        Returns:
            int: Number of items.
        """
        return len(self.d)

    def __iter__(self):
        """

        Returns:
            Iterator: Key iterator.
        """
        return iter(self.d)

    def copy(self):
        return type(self)(self.d)

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
            return Bunch({k: self.d.get(k, v) for k, v in keys.items()})
        else:
            return Bunch({k: self.d[k] for k in keys if k in self.d})

    def set_defaults(self, keys):
        """
        Set the value of any missing `keys`, then get a `Bunch` mapping all `keys` to their values.

        Args:
            keys (Mapping[str, Any]): Item keys, mapping to their default values.

        Returns:
            Bunch: Mapping of `keys` to their values, with set default values if missing.
        """
        return Bunch({k: self.d.setdefault(k, v) for k, v in keys.items()})

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
            return Bunch({k: self.d.pop(k, v) for k, v in keys.items()})
        else:
            return Bunch({k: self.d.pop(k) for k in keys if k in self.d})

    def __ixor__(self, keys):
        """
        Delete the items for `keys`.

        Args:
            keys (Iterable[str]): Item keys.
        """
        self.pop_items(keys)
        return self

    def __xor__(self, keys):
        """
        Get a copy with the items for `keys` deleted.

        Args:
            keys (Iterable[str]): Item keys.

        Returns:
            A `Bunch` with the same items except those in `keys`.
        """
        res = self.copy()
        self.pop_items(keys)
        return res

    def merge(self, other, op):
        """
        Update items from `other`, applying the binary `op` to `(self[key], other[key])` for each `key` both contain.

        Args:
            other (Mapping[str, Any]): `Mapping` to merge from.
            op ((Any, Any) -> Any): Merge operator, applied as `op(self_val, other_val)`.
        """
        for k, v in other.items():
            if k in self.d:
                self.d[k] = op(self.d[k], v)
            else:
                self.d[k] = v


class Op(object):
    def __init__(self, op, inplace):
        self.op = op
        self.inplace = inplace

    def __get__(self, obj, objtype=None):
        def apply(self_, other):
            if self.inplace:
                res = self_
            else:
                res = self_.copy()
            res.merge(self_, other, self.op)
            return res

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
