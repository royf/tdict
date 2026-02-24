from abc import ABC
from collections.abc import Iterator
from collections.abc import MutableMapping

__all__ = ['Tmap']


class TMutableMapping(MutableMapping, ABC):
    __contains__ = MutableMapping.__contains__
    keys = MutableMapping.keys
    items = MutableMapping.items
    values = MutableMapping.values
    get = MutableMapping.get
    __eq__ = MutableMapping.__eq__
    __ne__ = MutableMapping.__ne__
    pop = MutableMapping.pop
    popitem = MutableMapping.popitem
    clear = MutableMapping.clear
    update = MutableMapping.update
    setdefault = MutableMapping.setdefault


class Tmap(TMutableMapping, ABC):
    """
    Tree of `MutableMapping`s.

    Items of `str` keys can be accessed either as attributes or as items.
    The tree can be accessed recursively using `tuple` keys.
    """

    class ShallowView(MutableMapping):
        def __init__(self, tmap):
            self._tmap = tmap

        def __getitem__(self, key):
            return super(Tmap, self._tmap).__getitem__(key)

        def __setitem__(self, key, val):
            super(Tmap, self._tmap).__setitem__(key, val)

        def __delitem__(self, key):
            super(Tmap, self._tmap).__delitem__(key)

        def __len__(self):
            return super(Tmap, self._tmap).__len__()

        def __iter__(self):
            return super(Tmap, self._tmap).__iter__()

    def as_shallow(self):
        """
        Return a shallow view of this `Tmap` node.

        Returns:
            MutableMapping: A shallow view of this node.
        """
        return self.ShallowView(self)

    @classmethod
    def from_map_tree(cls, map_tree, through=None):
        """
        Construct a `Tmap` from a tree of `Mapping`s.

        Args:
            map_tree (MutableMapping | Any): Tree of `MutableMapping`s to construct from.
            through (set[type]): Types of non-`MutableMapping` nodes to traverse through when constructing.

        Returns:
            Tmap: Constructed `Tmap`.
        """
        if isinstance(map_tree, MutableMapping):
            res = cls()
            for k, v in map_tree.items():
                res.as_shallow()[k] = cls.from_map_tree(v, through=through)
        elif through is not None and (t := type(map_tree)) in through:
            res = t(cls.from_map_tree(v, through=through) for v in map_tree)
        else:
            res = map_tree
        return res

    def to_map_tree(self, shallow_type=dict, through=None):
        """
        Convert this `Tmap` to a tree of shallow `MutableMapping`s.

        Args:
            shallow_type (type): `MutableMapping` type to use for shallow nodes.
            through (set[type]): Types of non-`Tmap` nodes to traverse through when converting.

        Returns:
            MutableMapping: Tree of `MutableMapping`s corresponding to this `Tmap`.
        """
        res = shallow_type()
        for k, v in self.as_shallow().items():
            if isinstance(v, Tmap):
                res[k] = v.to_map_tree(shallow_type, through)
            elif through is not None and (t := type(v)) in through:
                res[k] = t(v.to_map_tree(shallow_type, through) for v in v)
            else:
                res[k] = v
        return res

    def __str__(self):
        """

        Returns:
            str: Informal string representation.
        """
        return f'{type(self).__name__}({", ".join(f"{k}={v}" for k, v in self.as_shallow().items())})'

    def __repr__(self):
        """

        Returns:
            str: String representation.
        """
        return f'''{type(self).__name__}({", ".join(
            f"{k if isinstance(k, str) and k.isidentifier() else repr(k)}={v!r}"
            for k, v in self.as_shallow().items())})'''

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
                        return self.as_shallow()[key[0]]
                    else:
                        child = self.as_shallow()[key[0]]
                        if not isinstance(child, Tmap):
                            raise KeyError(key)
                        return child[key[1:]]
                except KeyError:
                    raise KeyError(key) from None
        else:
            return self.as_shallow()[key]

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
                        self.as_shallow()[key[0]] = val
                    else:
                        try:
                            child = self.as_shallow()[key[0]]
                        except KeyError:
                            child = type(self)()
                            self.as_shallow()[key[0]] = child
                        if not isinstance(child, Tmap):
                            raise KeyError(key)
                        child[key[1:]] = val
                except KeyError:
                    raise KeyError(key) from None
        else:
            self.as_shallow()[key] = val

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
                        del self.as_shallow()[key[0]]
                    else:
                        child = self.as_shallow()[key[0]]
                        if not isinstance(child, Tmap):
                            raise KeyError(key)
                        del child[key[1:]]
                except KeyError:
                    raise KeyError(key) from None
        else:
            del self.as_shallow()[key]

    def __len__(self):
        """

        Returns:
            int: Number of items.
        """
        return sum(1 for _ in self)

    def __iter__(self):
        """

        Returns:
            Iterator: Key iterator.
        """
        for k, child in self.as_shallow().items():
            if isinstance(child, Tmap):
                for k_ in child:
                    yield k, *k_
            else:
                yield k,

    def copy(self):
        """

        Returns:
            Tmap: Copy of this `Tmap`.
        """
        res = type(self)()
        res.update(self)
        return res

    def update(self, other, op=None):
        """
        Update items from `other`, applying the binary `op` to value pairs from `self` and `other`, in this order.
        For each pair of leaf items, `(self_key, self_val)` and `(other_key, other_val)`,
          such that one key is a prefix and one key an extension of it,
          the result will have an item mapping the extension key to `op(self_val, other_val)`.
        The result will also have all leaf items in either source that have no prefix leaf items.

        Args:
            other (Tmap | Any): `Tmap` to update from.
            op ((Any, Any) -> Any): Update operator, applied as `op(self_val, other_val)`.
                Default: Choose the `other` value.
        """
        if op is None:
            op = lambda x, y: y
        if isinstance(other, Tmap):
            for k, other_child in other.as_shallow().items():
                try:
                    self_child = self.as_shallow()[k]
                except KeyError:
                    if isinstance(other_child, Tmap):
                        new_child = other_child.copy()
                    else:
                        new_child = other_child
                else:
                    if isinstance(self_child, Tmap):
                        self_child.update(other_child, op)
                        continue
                    elif isinstance(other_child, Tmap):
                        new_child = type(other_child)()
                        super(Tmap, new_child).update((k_, op(self_child, v_)) for k_, v_ in other_child.items())
                    else:
                        new_child = op(self_child, other_child)
                self.as_shallow()[k] = new_child
        else:
            super().update((k, op(v, other)) for k, v in self.items())
