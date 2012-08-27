from django.forms.widgets import TextInput

from django_mongoengine.forms.fields import DictField
from django_mongoengine.forms.widgets import Dictionary, SubDictionary, Pair


class DictFieldSavingTestCase(MongoTestCase):
    """
    TestCase class that tests for DictField object format when saved to Mongo
    """
    def __init__(self, methodName='rundictsaving'):
        self.field = DictField({
            'required': False,
            'initial': {
                'key': 'value'
                }
            })
        super(SimpleDictFieldRenderingTestCase, self).__init__()

    def check_structure(self):
        assert isinstance(self.field.widget, Dictionary), 'widget is not a Dictionary'
        assert len(self.field.widget.widgets) is 1, 'widgets list is anormally size : %s' % len(self.field.widget.widgets)
        assert isinstance(self.field.widget.widgets[0], Pair), 'sub-widget is not a Pair'
        assert isinstance(self.field.widget.widgets[0].widgets[0], TextInput), 'Pair sub-widget[0] is not a TextInput'
        assert isinstance(self.field.widget.widgets[0].widgets[1], TextInput), 'Pair sub-widget[1] is not a TextInput'

    def check_ouput(self):
        valid = {
            '[[key1,value1],[key2,value2],[key2,value2],[key1,value1]]' : {
                'key1': 'value1',
                'key2': 'value2',
                'key3': 'value3'
            },
            '[[key1,value1],[skey,[[skey1,svalue1],[skey2,svalue2],[skey3,svalue3]]],[key2,value2],[key3,value3]]' : {
                'key1': 'value1',
                'skey': {
                        'skey1': 'svalue1',
                        'skey2': 'svalue2',
                        'skey3': 'svalue3'
                    },
                'key2': 'value2',
                'key3': 'value3'
            },
            '[a,[b,[c,[d,[e,[f,g]]]]]]' : {
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
        #TODO : invalid inputs ?
        invalid = {}

        # test valid inputs
        for input, output in valid.items():
            self.assertEqual(self.field.clean(self._from_str_to_list(input)), output)
        # test invalid inputs
        # for input, errors in invalid.items():
        #     with self.assertRaises(ValidationError) as context_manager:
        #         required.clean(input)
        #     self.assertEqual(context_manager.exception.messages, errors)

        #     with self.assertRaises(ValidationError) as context_manager:
        #         optional.clean(input)
        #     self.assertEqual(context_manager.exception.messages, errors)

    def _from_str_to_list(self,s):
        if s[0] is '[':
            return [self._from_str_to_list(el) for el in s[1:-1].split(',')]
        else:
            return [el for el in s.split(',')]
        

# class DictFieldRenderTestCase(MongoTestCase):
#     """
#     TestCase class that tests rendering of DictField objects
#     """
#     def __init__(self, methodName='rundictsaving'):
#         super(SimpleDictFieldSavingTestCase, self).__init__()
#         self.html_template = {
#             'template1': '',
#             'template2': '',
#             }
        
#     def check_