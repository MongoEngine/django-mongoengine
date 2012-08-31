from django.forms.widgets import TextInput, SelectMultiple, MultiWidget, Media
from django.utils.safestring import mark_safe

from collections import OrderedDict
import re

import pdb

#the list of JavaScript files to insert to render any Dictionary widget
MEDIAS = ('jquery-1.8.0.min.js', 'dict.js')


class Dictionary(MultiWidget):
    """
    A widget representing a dictionary field
    """

    def __init__(self, schema=None, no_schema=1, max_depth=None, flags=None, sub_choices=None, attrs=None):
        # schema -- A dictionary representing the future schema of
        #            the Dictionary widget. It is responsible for the
        #            creation of subwidgets.
        # no_schema -- An integer that can take 3 values : 0,1,2.
        #               0 means that no schema was passed.
        #               1 means that the schema passed was the default
        #               one. This is the default value.
        #               2 means that the schema passed was given
        #               by a parent widget, and that it actually
        #               represent data for rendering.
        #               3 means that the schema was rebuilt after
        #               retrieving form data.
        # max_depth -- An integer representing the max depth of
        #              sub-dicts. If passed, the system will
        #              prevent to save dictionaries with depths
        #              superior to this parameter.
        # flags -- A list of flags. Available values :
        #               - 'FORCE_SCHEMA' : would force dictionaries
        #                 to keep a certain schema. Only Pair fields
        #                 could be added.
        # sub_choices -- A dictionary describing a list of choices for
        #                a given key. The first matching key is
        #                concerned.

        #pdb.set_trace()
        self.no_schema = no_schema
        self.max_depth = max_depth if max_depth is not None and max_depth >= 0 else None
        self.flags = flags
        self.sub_choices = sub_choices
        widget_object = []
        if isinstance(schema, dict) and self.no_schema > 0:
            for key in schema:
                if isinstance(schema[key], dict):
                    widget_object.append(SubDictionary(schema=schema[key], max_depth=max_depth, attrs=attrs))
                else:
                    widget_object.append(Pair(attrs=attrs))
        else:
            widget_object.append(Pair(attrs=attrs))

        super(Dictionary, self).__init__(widget_object, attrs)

    def decompress(self, value):
        if value and isinstance(value, dict):
            value = self.dict_sort(value)
            value = value.items()

            #if the schema in place wasn't passed by a parent widget, we need to rebuild it
            if self.no_schema < 2:
                self.update_widgets(value, erase=True)
            return value
        else:
            return []

    def render(self, name, value, attrs=None):
        if not isinstance(value, list):
            value = self.decompress(value)
        if self.is_localized:
            for widget in self.widgets:
                widget.is_localized = self.is_localized
        output = []
        final_attrs = self.build_attrs(attrs)
        id_ = final_attrs.get('id')
        for i, widget in enumerate(self.widgets):
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            suffix = widget.suffix
            if id_:
                final_attrs = dict(final_attrs, id='%s_%s_%s' % (id_, i, suffix))
            output.append(widget.render(name + '_%s_%s' % (i, suffix), widget_value, final_attrs))
        return mark_safe(self.format_output(name, output))

    def value_from_datadict(self, data, files, name):
        # I think the best solution here is to start from scratch, i mean :
        #     - erase every widget ;
        #    - create the new ones from the data dictionary
        # It would take into account every modification on the structure, and
        # make form repopulation automatic

        data_keys = data.keys()
        self.widgets = []
        html_indexes = []

        for data_key in data_keys:
            match = re.match(name + '_(\d+)_pair_0', data_key)
            if match is not None:
                self.widgets.append(Pair(attrs=self.attrs))
                html_indexes.append(match.group(1))
            else:
                match = re.match(name + '_(\d+)_subdict_0', data_key)
                if match is not None:
                        self.widgets.append(SubDictionary(no_schema=0, max_depth=self.max_depth, attrs=self.attrs))
                        html_indexes.append(match.group(1))
                else:
                    match = re.match(name + '_(\d+)_choice_0', data_key)
                    if match is not None:
                        self.widgets.append(ChoicePair(no_schema=0, attrs=self.attrs))
                        html_indexes.append(match.group(1))
        return [widget.value_from_datadict(data, files, name + '_%s_%s' % (html_indexes[i], widget.suffix)) for i, widget in enumerate(self.widgets)]

    def format_output(self, name, rendered_widgets):
        class_depth = ''
        if self.max_depth is not None:
            class_depth = 'depth_%s' % self.max_depth
        return '<ul id="id_%s" class="dictionary %s">\n' % (self.id_for_label(name), class_depth) + ''.join(rendered_widgets) + '</ul>\n' + \
               '<span id="add_id_%s" class="add_pair_dictionary">Add field</span>' % (self.id_for_label(name)) + \
               '<span id="add_sub_id_%s" class="add_sub_dictionary"> - Add subdictionary</span>' % (self.id_for_label(name))

    def update_widgets(self, keys, erase=False):
        if erase:
            self.widgets = []
        for k in keys:
            if (isinstance(k[1], dict)):
                self.widgets.append(SubDictionary(schema=k[1], no_schema=2, max_depth=self.max_depth, attrs=self.attrs))
            else:
                self.widgets.append(Pair(attrs=self.attrs))

    def _get_media(self):
        """
        Mimic the MultiWidget '_get_media' method, adding other media
        """
        media = Media(js=MEDIAS)
        for w in self.widgets:
            media = media + w.media
        return media
    media = property(_get_media)

    def dict_sort(self, d):
        if isinstance(d, dict):
            l = d.items()
            l.sort()
            k = OrderedDict()
            for item in l:
                k[item[0]] = self.dict_sort(item[1])
            return k
        else:
            return d


class Pair(MultiWidget):
    """
    A widget representing a key-value pair in a dictionary
    """

    #default for a pair
    key_type = TextInput
    value_type = TextInput
    suffix = 'pair'

    def __init__(self, attrs=None, **kwargs):
        widgets = [self.key_type()] if callable(self.key_type) else []
        if self.value_type in [TextInput, SelectMultiple]:
            widgets = [self.key_type(), self.value_type()]
        elif self.value_type == Dictionary:
            widgets = [self.key_type(), self.value_type(**kwargs)]
        super(Pair, self).__init__(widgets, attrs)

    #this method should be overwritten by subclasses
    def decompress(self, value):
        if value is not None:
            return list(value)
        else:
            return ['', '']

    def render(self, name, value, attrs=None):
        #pdb.set_trace()
        if self.is_localized:
            for widget in self.widgets:
                widget.is_localized = self.is_localized
        if not isinstance(value, list):
            value = self.decompress(value)
        output = []
        final_attrs = self.build_attrs(attrs)
        id_ = final_attrs.get('id')
        for i, widget in enumerate(self.widgets):
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            if id_:
                final_attrs = dict(final_attrs, id='%s_%s' % (id_, i))
            output.append(widget.render(name + '_%s' % i, widget_value, final_attrs))
        return mark_safe(self.format_output(output, name))

    def value_from_datadict(self, data, files, name):
        return [widget.value_from_datadict(data, files, name + '_%s' % i) for i, widget in enumerate(self.widgets)]

    def format_output(self, rendered_widgets, name):
        return '<li>' + ' : '.join(rendered_widgets) + '<span class="del_pair" id="del_%s"> - Delete</span></li>\n' % name


class SubDictionary(Pair):
    """
    A widget representing a key-value pair in a dictionary, where value is a dictionary
    """
    key_type = TextInput
    value_type = Dictionary
    suffix = 'subdict'

    def __init__(self, schema={'key': 'value'}, no_schema=1, max_depth=None, attrs=None):
        super(SubDictionary, self).__init__(attrs=attrs, schema=schema, no_schema=no_schema, max_depth=max_depth)

    def decompress(self, value):
        if value is not None:
            return list(value)
        else:
            return ['', {}]

    def format_output(self, rendered_widgets, name):
        #pdb.set_trace()
        return '<li>' + ' : '.join(rendered_widgets) + '<span class="del_dict" id="del_%s"> - Delete</span></li>\n' % name


class StaticPair(Pair):
    """
    A widget representing a key-value pair in a dictionary, where key is just text
    (this is only relevant when FORCE_SCHEMA flag is used)
    """

    key_type = ''
    value_type = TextInput
    suffix = 'static'

    def __init__(self, attrs=None):
        super(StaticPair, self).__init__(attrs=attrs)

    def decompress(self,value):
        if value is not None:
            return list(value)
        else:
            return ['']

    def format_output(self, rendered_widgets, name):
        #pdb.set_trace()
        return '<li>%s : ' + rendered_widgets[0] + '<span class="del_static" id="del_%s"> - Delete</span></li>\n' % (self.key_type, name)
