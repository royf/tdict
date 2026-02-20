from collections.abc import Iterator
from collections.abc import MutableMapping


class Tmap(MutableMapping):
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
                        return type(child).__getitem__(child, key[1:])
                except KeyError:
                    raise KeyError(key) from None
        else:
            return super().__getitem__(key)

        # Iterative version:
        # try:
        #     node = self
        #     if isinstance(key, tuple):
        #         if len(key) == 0:
        #             return self
        #         for k in key[:-1]:
        #             node = super(Tmap, node).__getitem__(k)
        #             if not isinstance(node, Tmap):
        #                 raise KeyError(k)
        #         leaf_key = key[-1]
        #     else:
        #         leaf_key = key
        #     return super(Tmap, node).__getitem__(leaf_key)
        # except KeyError:
        #     raise KeyError(key) from None

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
                        child = super().__getitem__(key[0])
                        if not isinstance(child, Tmap):
                            raise KeyError(key)
                        type(child).__setitem__(child, key[1:], val)
                except KeyError:
                    raise KeyError(key) from None
        else:
            super().__setitem__(key, val)

        # Iterative version:
        # try:
        #     node: Tmap = self
        #     if isinstance(key, tuple):
        #         if len(key) == 0:
        #             raise KeyError("cannot set root")
        #         for k in key[:-1]:
        #             try:
        #                 node = super(Tmap, node).__getitem__(k)
        #             except KeyError:
        #                 child = type(node)()
        #                 super(Tmap, node).__setitem__(k, child)
        #                 node = child
        #             else:
        #                 if not isinstance(node, Tmap):
        #                     raise KeyError(k)
        #         leaf_key = key[-1]
        #     else:
        #         leaf_key = key
        #     super(Tmap, node).__setitem__(leaf_key, val)
        # except KeyError:
        #     raise KeyError(key) from None

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
                        type(child).__delitem__(child, key[1:])
                except KeyError:
                    raise KeyError(key) from None
        else:
            super().__delitem__(key)

        # Iterative version:
        # try:
        #     node = self
        #     if isinstance(key, tuple):
        #         if len(key) == 0:
        #             raise KeyError("cannot delete root")
        #         for k in key[:-1]:
        #             node = super(Tmap, node).__getitem__(k)
        #             if not isinstance(node, Tmap):
        #                 raise KeyError(k)
        #         leaf_key = key[-1]
        #     else:
        #         leaf_key = key
        #     super(Tmap, node).__delitem__(leaf_key)
        # except KeyError:
        #     raise KeyError(key) from None

    def __len__(self):
        """

        Returns:
            int: Number of items.
        """
        return sum(len(v) if isinstance(v, Tmap) else 1 for v in super().values())

    def __iter__(self):
        """

        Returns:
            Iterator: Key iterator.
        """
        for k, v in super().items():
            if isinstance(v, Tmap):
                for k_ in iter(v):
                    yield k, *k_
            else:
                yield k

    def merge(self, other, op):
        """
        Update items from `other`, applying the binary `op` to value pairs from `self` and `other`, in this order.
        For each pair of leaf items, `(self_key, self_val)` and `(other_key, other_val)`,
          such that one key is a prefix and one key an extension of it,
          the result will have an item mapping the extension key to `op(self_val, other_val)`.
        The result will also have all leaf items in either source that have no prefix leaf items.

        Args:
            other (Tmap): `Tmap` to merge from.
            op ((Any, Any) -> Any): Merge operator, applied as `op(self_val, other_val)`.

        Returns:
            Tmap: Updated `Tmap`.
        """
        if isinstance(other, Tmap):
            for k, other_child in super(Tmap, other).items():
                if super().__contains__(k):
                    self_child = super().__getitem__(k)
                    if isinstance(self_child, Tmap):
                        new_child = type(self_child).merge(self_child, other_child, op)
                    elif isinstance(other_child, Tmap):
                        new_child = type(other_child)().update((
                            (k_, op(self_child, v_))
                            for k_, v_ in type(other_child).items(other_child)))
                    else:
                        new_child = op(self_child, other_child)
                elif isinstance(other_child, Tmap):
                    new_child = type(other_child)().update(other_child)
                else:
                    new_child = other_child
                super().__setitem__(k, new_child)
        else:
            type(self).update(self, ((k, op(v, other)) for k, v in type(self).items(self)))
        return self
