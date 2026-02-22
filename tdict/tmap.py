from abc import ABC
from collections.abc import Iterator
from collections.abc import MutableMapping as abcMM


class MutableMapping(abcMM, ABC):
    __contains__ = abcMM.__contains__
    keys = abcMM.keys
    items = abcMM.items
    values = abcMM.values
    get = abcMM.get
    __eq__ = abcMM.__eq__
    __ne__ = abcMM.__ne__
    pop = abcMM.pop
    popitem = abcMM.popitem
    clear = abcMM.clear
    update = abcMM.update
    setdefault = abcMM.setdefault


class Tmap(MutableMapping, ABC):
    """
    Tree of `Bunch`.

    Items of `str` keys can be accessed either as attributes or as items.
    The tree can be accessed recursively using `tuple` keys.
    """

    def __getitem__(self, key):
        """

        Args:
            key (str | tuple): Item key. A `tuple` `key` is used for recursive access.

        Returns:
            Item value.

        Raises:
            KeyError: If `key`'s path traverses a leaf.
        """
        if isinstance(key, tuple):
            if len(key) == 0:
                return self
            else:
                try:
                    if len(key) == 1:
                        return super().__getitem__(key[0])
                    else:
                        child = super().__getitem__(key[0])
                        if not isinstance(child, Tmap):
                            raise KeyError(key)
                        return child[key[1:]]
                except KeyError:
                    raise KeyError(key) from None
        else:
            return super().__getitem__(key)

    def __setitem__(self, key, val):
        """

        Args:
            key (str | tuple): Item key. A `tuple` `key` is used for recursive access, creating nodes as needed.
            val: Item value.

        Raises:
            KeyError: `key` is an empty `tuple` or its path traverses a leaf.
        """
        if isinstance(key, tuple):
            if len(key) == 0:
                raise KeyError("cannot set root")
            else:
                try:
                    if len(key) == 1:
                        super().__setitem__(key[0], val)
                    else:
                        try:
                            child = super().__getitem__(key[0])
                        except KeyError:
                            child = type(self)()
                            super().__setitem__(key[0], child)
                        if not isinstance(child, Tmap):
                            raise KeyError(key)
                        child[key[1:]] = val
                except KeyError:
                    raise KeyError(key) from None
        else:
            super().__setitem__(key, val)

    def __delitem__(self, key):
        """

        Args:
            key (str | tuple): Item key. A `tuple` `key` is used for recursive access.

        Raises:
            KeyError: `key` is an empty `tuple` or its path traverses a leaf.
        """
        if isinstance(key, tuple):
            if len(key) == 0:
                raise KeyError("cannot delete root")
            else:
                try:
                    if len(key) == 1:
                        super().__delitem__(key[0])
                    else:
                        child = super().__getitem__(key[0])
                        if not isinstance(child, Tmap):
                            raise KeyError(key)
                        del child[key[1:]]
                except KeyError:
                    raise KeyError(key) from None
        else:
            super().__delitem__(key)

    def __len__(self):
        """

        Returns:
            int: Number of items.
        """
        return sum(1 for _ in iter(self))

    def __iter__(self):
        """

        Returns:
            Iterator: Key iterator.
        """
        for k in super().__iter__():
            child = super().__getitem__(k)
            if isinstance(child, Tmap):
                for k_ in iter(child):
                    yield k, *k_
            else:
                yield k,

    def copy(self):
        res = type(self)()
        res.update(self)
        return res

    def merge(self, other, op):
        """
        Update items from `other`, applying the binary `op` to value pairs from `self` and `other`, in this order.
        For each pair of leaf items, `(self_key, self_val)` and `(other_key, other_val)`,
          such that one key is a prefix and one key an extension of it,
          the result will have an item mapping the extension key to `op(self_val, other_val)`.
        The result will also have all leaf items in either source that have no prefix leaf items.

        Args:
            other (Tmap | Any): `Tmap` to merge from.
            op ((Any, Any) -> Any): Merge operator, applied as `op(self_val, other_val)`.
        """
        if isinstance(other, Tmap):
            for k in super(Tmap, other).__iter__():
                other_child = super(Tmap, other).__getitem__(k)
                try:
                    self_child = super().__getitem__(k)
                except KeyError:
                    if isinstance(other_child, Tmap):
                        new_child = other_child.copy()
                    else:
                        new_child = other_child
                else:
                    if isinstance(self_child, Tmap):
                        self_child.merge(other_child, op)
                        continue
                    elif isinstance(other_child, Tmap):
                        new_child = type(other_child)()
                        new_child.update(((k_, op(self_child, v_)) for k_, v_ in other_child.items()))
                    else:
                        new_child = op(self_child, other_child)
                super().__setitem__(k, new_child)
        else:
            self.update(((k, op(v, other)) for k, v in self.items()))
