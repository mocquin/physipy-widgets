
import unittest

from traitlets import TraitError

from physipy import utils, units, m, s
from physipywidgets.qipywidgets import QuantityText, FDQuantityText


ms = units['ms']
mm = units['mm']


class TestQuantityText(unittest.TestCase):

    #@classmethod
    #def setUpClass(cls):
    #    a = 4*m
    #    a.favunit = mm
    #    cls.a = a
    #    cls.qt = QuantityText(a, description="Text")

    def setUp(self):
        a = 4*m
        a.favunit = mm
        self.a = a
        self.qt = QuantityText(a, description="Text")


    def test_creation(self):
        
        # right after init
        self.assertEqual(self.qt.value, self.a)
        self.assertTrue(utils.hard_equal(self.qt.favunit, mm))
        self.assertEqual(self.qt.text.value, '4000.0 mm')

    def test_new_value_with_other_dimension(self):
        self.qt.value = 5*s
        self.assertEqual(self.qt.value,  5*s)
        self.assertTrue(self.qt.favunit is None)
        self.assertEqual(self.qt.text.value, '5 s')

    def test_new_value_with_same_dimension(self):
        # change value with same dimension
        self.qt.value = 10*m
        self.assertEqual(self.qt.value,  10*m)
        self.assertTrue(utils.hard_equal(self.qt.favunit, mm))
        self.assertEqual(self.qt.text.value, '10000.0 mm')

    def test_overwrite_favunit_different(self):
        # overwrite favunit at creation, with different dimension
        a = 4*m
        qt = QuantityText(a, description="Text", favunit=ms)
        self.assertTrue(utils.hard_equal(qt.favunit, ms))
        self.assertEqual(qt.text.value, "4000.0 ms*m/s")

    def test_overwrite_favunit_same(self):
        # overwrite favunit at creation, with same dimension
        a = 4*m
        a.favunit = ms
        qt = QuantityText(a, description="Text", favunit=mm)
        self.assertTrue(utils.hard_equal(qt.favunit, mm))
        self.assertEqual(qt.text.value,  "4000.0 mm")


class TestFDQuantityText(unittest.TestCase):

    def setUp(self):
        a = 4*m
        a.favunit = mm
        self.a = a
        self.qt = FDQuantityText(a, description="Text")
    
    def test_raise_other_dim(self):
        with self.assertRaises(TraitError):
            self.qt.value = 5*s



if __name__ == "__main__":
    unittest.main()
