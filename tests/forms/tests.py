import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

from django import test
test.utils.setup_test_environment()
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.forms.fields import TextInput

from django_mongoengine.tests import MongoTestCase
from django_mongoengine.forms.fields import DictField
from django_mongoengine.forms.widgets import Dictionary, SubDictionary, Pair

#TODO : test for max_depth


class DictFieldTest(MongoTestCase):
    """
    TestCase class that tests a DictField object
    """
    def __init__(self, methodName='rundict'):
        super(DictFieldTest, self).__init__(methodName)

    def test_ouput(self):
        """
        Test the output of a DictField
        """
        self._init_field()
        max_depth_test = 2
        #valid input/outpout
        valid_input = {
            '[[key1,value1],[key2,value2],[key3,value3]]':
                [['key1', 'value1'], ['key2', 'value2'], ['key3', 'value3']],
            '[[key1,value1],[skey,[[skey1,svalue1],[skey2,svalue2],[skey3,svalue3]]],[key2,value2],[key3,value3]]':
                [['key1', 'value1'], ['skey', [['skey1', 'svalue1'], ['skey2', 'svalue2'], ['skey3', 'svalue3']]], ['key2', 'value2'], ['key3', 'value3']],
            '[[a,[[b,[[c,[[d,[[e,[[f,g]]]]]]]]]]]]':
                [['a', [['b', [['c', [['d', [['e', [['f', 'g']]]]]]]]]]]],
        }
        valid_output = {
            '[[key1,value1],[key2,value2],[key3,value3]]': {
                'key1': 'value1',
                'key2': 'value2',
                'key3': 'value3'
            },
            '[[key1,value1],[skey,[[skey1,svalue1],[skey2,svalue2],[skey3,svalue3]]],[key2,value2],[key3,value3]]': {
                'key1': 'value1',
                'skey': {
                        'skey1': 'svalue1',
                        'skey2': 'svalue2',
                        'skey3': 'svalue3'
                    },
                'key2': 'value2',
                'key3': 'value3'
            },
            '[[a,[[b,[[c,[[d,[[e,[[f,g]]]]]]]]]]]]': {
                'a': {
                    'b': {
                        'c': {
                            'd': {
                                'e': {
                                    'f': 'g'
                                }
                            }
                        }
                    }
                }
            },
        }
        #invalid input/message
        invalid_input = {
            '[[key1,value1],[$key2,value2]]': [['key1', 'value1'], ['$key2', 'value2']],
            '[[key1,value1],[_key2,value2]]': [['key1', 'value1'], ['_key2', 'value2']],
            '[[key1,value1],[k.ey2,value2]]': [['key1', 'value1'], ['k.ey2', 'value2']],
            '[[keykeykeykeykeykeykeykeykeykeykey,value1],[key2,value2]]': [['keykeykeykeykeykeykeykeykeykeykey', 'value1'], ['key2', 'value2']],
            '[[err,value1],[key2,value2]]': [['err', 'value1'], ['key2', 'value2']],
            '[[errmsg,value1],[key2,value2]]': [['errmsg', 'value1'], ['key2', 'value2']],
            '[[key1,[key2,[key3,[key4,value4]]]]]': [['key1', [['key2', [['key3', [['key4', 'value4']]]]]]]],
        }
        invalid_message = {
            '[[key1,value1],[$key2,value2]]': [u'Ensure the keys do not begin with : ["$","_"].'],
            '[[key1,value1],[_key2,value2]]': [u'Ensure the keys do not begin with : ["$","_"].'],
            '[[key1,value1],[k.ey2,value2]]': [self.field.error_messages['illegal'] % self.field.illegal_characters],
            '[[keykeykeykeykeykeykeykeykeykeykey,value1],[key2,value2]]': [self.field.error_messages['length'] % self.field.key_limit],
            '[[err,value1],[key2,value2]]': [self.field.error_messages['invalid_key'] % self.field.invalid_keys],
            '[[errmsg,value1],[key2,value2]]': [self.field.error_messages['invalid_key'] % self.field.invalid_keys],
            '[[key1,[key2,[key3,[key4,value4]]]]]': [self.field.error_messages['depth'] % max_depth_test],
        }

        # test valid inputs
        for input, output in valid_output.items():
            out = self.field.clean(valid_input[input])
            assert isinstance(out, dict), 'output should be a dictionary'
            self.assertDictEqual(out, output)
        # test invalid inputs
        self._init_field(depth=max_depth_test)
        for input, input_list in invalid_input.items():
            with self.assertRaises(ValidationError) as context_manager:
                self.field.clean(input_list)
            self.assertEqual(context_manager.exception.messages, invalid_message[input])

    def test_rendering(self):
        """
        Test the structure of a widget, after having passed a data dictionary
        """
        self._init_field()
        #contains the POST data dicts
        data_inputs = {
            'data1': {
                u'widget_name_0_subdict_0': [u'a'],
                u'widget_name_0_subdict_1_0_subdict_0': [u'b'],
                u'widget_name_0_subdict_1_0_subdict_1_0_pair_0': [u'f'],
                u'widget_name_0_subdict_1_0_subdict_1_0_pair_1': [u'g'],
            }
        }
        #contains the data dicts
        data_dicts = {
            'data1': {
                u'a': {
                    u'b': {
                        u'f': u'g'
                    }
                }
            }
        }
        #contains structures of output
        output_structures = {
            'data1': {
                'type': 'Dictionary',
                'widgets': [{'type': 'SubDictionary',
                      'widgets': [{'type': 'TextInput'}, {'type': 'Dictionary',
                                                    'widgets': [{'type': 'SubDictionary',
                                                          'widgets': [{'type': 'TextInput'}, {'type': 'Dictionary',
                                                                                        'widgets': [{'type': 'Pair', 'widgets':[{'type': 'TextInput'}, {'type': 'TextInput'}]}]
                                                                    }]
                                                            }]
                                }]
                        }]
            }
        }

        for data, datadict in data_inputs.items():
            self.field.widget.render('widget_name', self.field.widget.value_from_datadict(datadict, {}, 'widget_name'))
            self._check_structure(self.field.widget, output_structures[data])
            self.field.widget.render('widget_name', data_dicts[data])
            self._check_structure(self.field.widget, output_structures[data])

    def _init_field(self, depth=None):
        validate = [RegexValidator(regex='^[^$_]', message=u'Ensure the keys do not begin with : ["$","_"].', code='invalid_start')]
        self.field = DictField(**{
            'required': False,
            'initial': {
                'k': 'v',
                'kk': {'kkk': 'vvv'}
            },
            'validators': validate,
        })
        if depth is not None:
            self.field.widget = Dictionary(max_depth=depth)
            self.field.max_depth = depth

    def _check_structure(self, widget, structure):
        assert isinstance(structure, dict), 'error, the comparative structure should be a dictionary'
        assert isinstance(widget, eval(structure['type'])), 'widget should be a %s' % structure['type']
        if 'widgets' in structure.keys():
            assert isinstance(structure['widgets'], list), 'structure field "widgets" should be a list'
            assert isinstance(widget.widgets, list), 'widget.widgets should be a list'
            for i, w in enumerate(widget.widgets):
                self._check_structure(w, structure['widgets'][i])
