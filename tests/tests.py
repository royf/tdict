import unittest

from tdict import Tdict


class TestInitialization(unittest.TestCase):
    def test_basic_init(self):
        d = Tdict({'aa': 1}, {'bb': {'cc': 3}}, dd=4)
        self.assertEqual(d.aa, 1)
        self.assertEqual(d.bb.cc, 3)
        self.assertEqual(d.dd, 4)

    def test_update_init(self):
        d = Tdict({'aa': 1, 'bb': 2, 'dd': {'ee': 5}}, {'bb': {'cc': 3}}, dd=4)
        self.assertEqual(d.aa, 1)
        self.assertEqual(d.bb.cc, 3)
        self.assertEqual(d.dd, 4)


class TestClassAttributes(unittest.TestCase):
    def test_basic_attr(self):
        d = Tdict({'aa': {'bb': 2}})
        self.assertTrue(d.DEEP)
        self.assertIsNone(d.DEFAULT_FACTORY)

    def test_class(self):
        d1 = Tdict({'aa': {'bb': 2}})
        d2 = d1.copy()
        self.assertIsInstance(d1, Tdict)
        self.assertIsInstance(d2, Tdict)
        self.assertIsNot(type(d1), Tdict)
        self.assertIsNot(type(d2), Tdict)
        self.assertEqual(d1, d2)
        self.assertIsNot(d1, d2)
        self.assertIsNot(type(d2), type(d1))

    def test_set_attr(self):
        d1 = Tdict({'aa': {'bb': 2}})
        self.assertEqual(set(d1.keys()), {('aa', 'bb')})
        with self.assertRaises(KeyError) as e:
            d1.dd.append(4)
        self.assertIsInstance(e.exception, KeyError)
        d2 = d1.with_shallow()
        d3 = d1.with_default_factory(list)
        self.assertIs(d1, d2)
        self.assertIs(d1, d3)
        self.assertFalse(d1.DEEP)
        self.assertIs(d1.DEFAULT_FACTORY, list)
        self.assertEqual(set(d1.keys()), {'aa'})
        d1.dd.append(4)
        self.assertEqual(d1.dd, [4])

    def test_set_item(self):
        d = Tdict({'aa': {'bb': 2}})
        self.assertFalse('DEEP' in d)
        self.assertFalse('DEFAULT_FACTORY' in d)
        d.DEEP = False
        d.DEFAULT_FACTORY = list
        self.assertFalse(d.DEEP)
        self.assertTrue(type(d).DEEP)
        self.assertEqual(d.DEFAULT_FACTORY, list)
        self.assertIsNone(type(d).DEFAULT_FACTORY)
        self.assertEqual(set(d.keys()), {('aa', 'bb'), ('DEEP',), ('DEFAULT_FACTORY',)})
        with self.assertRaises(KeyError) as e:
            d.dd.append(4)
        self.assertIsInstance(e.exception, KeyError)

    def test_user_item(self):
        d = Tdict({'aa': {'bb': 2}})
        d.key = 1
        type(d).key = 3
        self.assertEqual(d.key, 1)
        self.assertEqual(type(d).key, 3)


class TestRepresentation(unittest.TestCase):
    def test_repr(self):
        d = Tdict(aa={'1': 'x'}, bb=2)
        self.assertEqual(str(d), "Tdict(aa=Tdict(1=x), bb=2)")
        self.assertEqual(repr(d), "Tdict(aa=Tdict('1'='x'), bb=2)")


class TestGet(unittest.TestCase):
    def test_basic_get(self):
        d = Tdict({'aa': {'bb': 2}})
        self.assertIs(d[()], d)
        self.assertEqual(d.aa, Tdict(bb=2))
        self.assertIs(d['aa'], d.aa)
        self.assertEqual(d.aa.bb, 2)
        self.assertEqual(d['aa']['bb'], 2)
        self.assertEqual(d['aa', 'bb'], 2)

    def test_fancy_get(self):
        d = Tdict({'a': Tdict(b=Tdict(c=3)), ('a', 'b', 'c'): 4})
        self.assertEqual(d[*'abc'], 3)
        self.assertEqual(d[(*'abc',),], 4)

    def test_deep_get(self):
        d = Tdict(
            aa=Tdict(bb=Tdict(cc=3), dd=Tdict().with_default_factory(int)),
            ee=Tdict(ff=Tdict()).with_default_factory(int))
        self.assertIs(d[()], d)
        self.assertEqual(d['aa', 'bb', 'cc'], 3)
        with self.assertRaises(KeyError) as e:
            _ = d['aa', 'bb', 'xx']
        self.assertIsInstance(e.exception, KeyError)
        self.assertEqual(d['aa', 'dd', 'xx'], 0)
        self.assertEqual(d['aa', 'dd', 'yy', 'zz'], 0)
        with self.assertRaises(KeyError) as e:
            _ = d['ee', 'ff', 'xx']
        self.assertIsInstance(e.exception, KeyError)
        d['aa', 'hh'] = {'ii': 9}
        with self.assertRaises(KeyError) as e:
            _ = d['aa', 'hh', 'ii']
        self.assertIsInstance(e.exception, KeyError)
        d2 = Tdict(
            aa=Tdict(bb=Tdict(cc=3), dd=Tdict(xx=0, yy=Tdict(zz=0))),
            ee=Tdict(ff=Tdict()))
        d2.aa.hh = {'ii': 9}
        self.assertEqual(d, d2)


class TestSet(unittest.TestCase):
    def test_basic_set(self):
        d = Tdict()
        d.aa = {'bb': 2}
        d['cc'] = 3
        d['dd', 'ee'] = 5
        d[7, 0.7, 0.77 + 0.07j, True, 'seven', ('se', 0.7, 'ven'), frozenset(range(7))] = 77
        with self.assertRaises(KeyError) as e:
            d['aa', 'bb'] = 22
        self.assertIsInstance(e.exception, KeyError)
        self.assertEqual(
            repr(d),
            "Tdict(aa={'bb': 2}, cc=3, dd=Tdict(ee=5), "
            "7=Tdict("
            "0.7=Tdict("
            "(0.77+0.07j)=Tdict("
            "True=Tdict("
            "seven=Tdict("
            "('se', 0.7, 'ven')=Tdict("
            "frozenset({0, 1, 2, 3, 4, 5, 6})=77)))))))")

    def test_fancy_set(self):
        d = Tdict()
        d[*'abc'] = 3
        d[(*'abc',),] = 4
        self.assertEqual(d.a.b.c, 3)
        # noinspection PyTypeChecker
        self.assertEqual(vars(d)[tuple('abc')], 4)


# TODO: add README examples and tests:
#   - delete
#   - membership
#   - advanced access
#   - iterators
#   - casting
#   - copying and exclusion
#   - updating
#   - subclassing
#   - serialization (pickle)
#   - objects of various types as keys and values
#   - pattern matching


if __name__ == '__main__':
    unittest.main()
