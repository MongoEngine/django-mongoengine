import re
from collections import OrderedDict

from django.forms.widgets import HiddenInput, Media, MultiWidget, TextInput
from django.utils.safestring import mark_safe

# The list of JavaScript files to insert to render any Dictionary widget
MEDIAS = ('jquery-1.8.0.min.js', 'dict.js', 'helper.js')
ADD_FIELD_VERBOSE = 'Add Field'
ADD_DICT_VERBOSE = ' - Add subdictionary'


class Dictionary(MultiWidget):
    """
    A widget representing a dictionary field
    """

    def __init__(
        self,
        schema=None,
        no_schema=1,
        max_depth=None,
        flags=None,
        sub_attrs=None,
        attrs=None,
        verbose_dict=None,
        verbose_field=None,
    ):
        """
        :param schema: A dictionary representing the future schema of
                       the Dictionary widget. It is responsible for the
                       creation of subwidgets.
        :param no_schema: An integer that can take 3 values : 0,1,2.
                          0 means that no schema was passed.
                          1 means that the schema passed was the default
                          one. This is the default value.
                          2 means that the schema passed was given
                          by a parent widget, and that it actually
                          represent data for rendering.
                          3 means that the schema was rebuilt after
                          retrieving form data.
        :param max_depth: An integer representing the max depth of
                          sub-dicts. If passed, the system will
                          prevent to save dictionaries with depths
                          superior to this parameter.
        :param flags:    A list of flags. Available values :
                         - 'FORCE_SCHEMA' : would force dictionaries
                            to keep a certain schema. Only Pair fields
                            could be added.
        :param sub_attrs:   A dictionary that contains the classes
                            for the keys (key.class) and the values
                            (value.class) of each pair
        :param verbose_field:   verbose for 'Add field'
        :param verbose_dict:    verbose for 'Add dict'
        """
        self.verbose_field = verbose_field or ADD_FIELD_VERBOSE
        self.verbose_dict = verbose_dict or ADD_DICT_VERBOSE
        self.no_schema = no_schema
        self.max_depth = max_depth if max_depth and max_depth >= 0 else None
        self.flags = flags or []
        self.sub_attrs = sub_attrs or {}

        if flags is not None and 'FORCE_SCHEMA' in flags:
            self.pair = StaticPair
            self.subdict = StaticSubDictionary
        else:
            self.pair = Pair
            self.subdict = SubDictionary

        widget_object = []
        if isinstance(schema, dict) and self.no_schema > 0:
            for key in schema:
                if isinstance(schema[key], dict):
                    widget_object.append(
                        self.subdict(
                            key_value=key,
                            schema=schema[key],
                            max_depth=max_depth,
                            sub_attrs=self.sub_attrs,
                            attrs=attrs,
                            verbose_field=self.verbose_field,
                            verbose_dict=self.verbose_dict,
                        )
                    )
                else:
                    widget_object.append(
                        self.pair(key_value=key, sub_attrs=self.sub_attrs, attrs=attrs)
                    )
        else:
            widget_object.append(self.pair(sub_attrs=self.sub_attrs, sattrs=attrs))

        super().__init__(widget_object, attrs)

    def decompress(self, value):
        if value and isinstance(value, dict):
            value = self.dict_sort(value)
            value = list(value.items())

            # If the schema in place wasn't passed by a parent widget
            # we need to rebuild it
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
        attrs = attrs or {}
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
            output.append(widget.render('%s_%s_%s' % (name, i, suffix), widget_value, final_attrs))
        return mark_safe(self.format_output(name, output))

    def value_from_datadict(self, data, files, name):
        """
        Process is:
            - erase every widget ;
            - create the new ones from the data dictionary

        It would take into account every modification on the structure, and
        make form repopulation automatic
        """
        data_keys = data.keys()
        self.widgets = []
        html_indexes = []
        prefix = 'st' if self.flags is not None and 'FORCE_SCHEMA' in self.flags else ''
        for data_key in data_keys:
            match = re.match(name + r'_(\d+)_%spair_0' % prefix, data_key)
            if match is not None:
                self.widgets.append(self.pair(sub_attrs=self.sub_attrs, attrs=self.attrs))
                html_indexes.append(match.group(1))
            else:
                match = re.match(name + r'_(\d+)_%ssubdict_0' % prefix, data_key)
                if match is not None:
                    self.widgets.append(
                        self.subdict(
                            sub_attrs=self.sub_attrs,
                            no_schema=0,
                            max_depth=self.max_depth,
                            flags=self.flags,
                            attrs=self.attrs,
                        )
                    )
                    html_indexes.append(match.group(1))

        return [
            widget.value_from_datadict(
                data, files, '%s_%s_%s' % (name, html_indexes[i], widget.suffix)
            )
            for i, widget in enumerate(self.widgets)
        ]

    def format_output(self, name, rendered_widgets):
        class_depth = ''
        if self.max_depth is not None:
            class_depth = 'depth_%s' % self.max_depth

        params = {
            'id': "id_%s" % self.id_for_label(name),
            'class_depth': class_depth,
            'widgets': ''.join(rendered_widgets),
            'add_id': 'add_id_%s' % self.id_for_label(name),
            'add_sub_id': 'add_sub_id_%s' % self.id_for_label(name),
            'add_field': ADD_FIELD_VERBOSE,
            'add_dict': ADD_DICT_VERBOSE,
        }

        if 'FORCE_SCHEMA' not in self.flags:
            actions = (
                """
<span id="%(add_id)s" class="add_pair_dictionary">%(add_field)s</span>
<span id="%(add_sub_id)s" class="add_sub_dictionary">
    %(add_dict)s
</span>
"""
                % params
            )
        else:
            actions = ''

        params['actions'] = actions

        return (
            """
<ul id="%(id)s" class="dictionary %(class_depth)s">
  %(widgets)s
</ul>
%(actions)s
"""
            % params
        )

    def update_widgets(self, keys, erase=False):
        # import pdb
        # pdb.set_trace()
        if erase:
            self.widgets = []
        for k in keys:
            if isinstance(k[1], dict):
                self.widgets.append(
                    self.subdict(
                        key_value=k[0],
                        schema=k[1],
                        no_schema=2,
                        max_depth=self.max_depth,
                        flags=self.flags,
                        sub_attrs=self.sub_attrs,
                        attrs=self.attrs,
                    )
                )
            else:
                self.widgets.append(
                    self.pair(sub_attrs=self.sub_attrs, key_value=k[1], attrs=self.attrs)
                )

    def _get_media(self):
        """
        Mimic the MultiWidget '_get_media' method, adding other media
        """
        if 'FORCE_SCHEMA' in self.flags:
            media = Media()
        else:
            media = Media(js=MEDIAS)

        for w in self.widgets:
            media = media + w.media
        return media

    media = property(_get_media)

    def dict_sort(self, d):
        if isinstance(d, dict):
            return OrderedDict([(k, self.dict_sort(v)) for k, v in sorted(d.items())])
        else:
            return d


class Pair(MultiWidget):
    """
    A widget representing a key-value pair in a dictionary
    """

    # default for a pair
    key_type = TextInput
    value_type = TextInput
    suffix = 'pair'

    def __init__(self, sub_attrs, key_value=None, attrs=None, **kwargs):
        widgets = [self.key_type()] if callable(self.key_type) else []
        if self.value_type in [TextInput, HiddenInput]:
            if sub_attrs:
                try:
                    widgets = [
                        self.key_type(attrs=sub_attrs['key']),
                        self.value_type(attrs=sub_attrs['value']),
                    ]
                except KeyError:
                    raise KeyError("improper synthax for sub_attrs parameter")
            else:
                widgets = [self.key_type(), self.value_type()]
        elif self.value_type == Dictionary:
            if sub_attrs:
                try:
                    widgets = [
                        self.key_type(attrs=sub_attrs['key']),
                        self.value_type(attrs=sub_attrs['value'], **kwargs),
                    ]
                except KeyError:
                    raise KeyError("improper synthax for sub_attrs parameter")
            else:
                widgets = [self.key_type(), self.value_type(**kwargs)]
        self.sub_attrs = sub_attrs
        # raise error here ?
        self.key_value = key_value if key_value is not None else ''
        super().__init__(widgets, attrs)

    # this method should be overwritten by subclasses
    def decompress(self, value):
        if value is not None:
            return list(value)
        else:
            return ['', '']

    def render(self, name, value, attrs=None):
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
        return [
            widget.value_from_datadict(data, files, name + '_%s' % i)
            for i, widget in enumerate(self.widgets)
        ]

    def format_output(self, rendered_widgets, name):
        return (
            '<li>'
            + ' : '.join(rendered_widgets)
            + '<span class="del_pair" id="del_%s"> - Delete</span></li>\n' % name
        )


class SubDictionary(Pair):
    """
    A widget representing a key-value pair in a dictionary, where value is a dictionary
    """

    key_type = TextInput
    value_type = Dictionary
    suffix = 'subdict'

    def __init__(self, sub_attrs, schema=None, **kwargs):
        if schema is None:
            schema = {'key': 'value'}
        super().__init__(schema=schema, sub_attrs=sub_attrs, **kwargs)

    def decompress(self, value):
        if value is not None:
            return list(value)
        else:
            return ['', {}]

    def format_output(self, rendered_widgets, name):
        params = {"widgets": ' : '.join(rendered_widgets), "del_id": "del_%s" % name}
        return (
            """
<li> %(widgets)s <span class="del_dict" id="%(del_id)s"> - Delete</span>
</li>"""
            % params
        )


class StaticPair(Pair):
    """
    A widget representing a key-value pair in a dictionary, where key is just
    text (this is only relevant when FORCE_SCHEMA flag is used)
    """

    key_type = HiddenInput
    value_type = TextInput
    suffix = 'stpair'

    # def __init__(self, key_value, attrs=None):
    #     super(StaticPair, self).__init__(key_value=key_value, attrs=attrs)

    def decompress(self, value):
        value = super().decompress(value)
        self.key_value = value[0]
        return value

    def format_output(self, rendered_widgets, name):
        params = {
            "html_class": self.sub_attrs.get('key', {}).get('class', ''),
            "key": self.key_value,
            "widgets": ''.join(rendered_widgets),
        }
        return (
            """
<li><span class="static_key %(html_class)s">%(key)s</span> :  %(widgets)s
</li>"""
            % params
        )


class StaticSubDictionary(SubDictionary):
    """
    A widget representing a key-value pair in a dictionary, where key is just
    text (this is only relevant when FORCE_SCHEMA flag is used)
    """

    key_type = HiddenInput
    value_type = Dictionary
    suffix = 'stsubdict'

    def decompress(self, value):
        value = super().decompress(value)
        self.key_value = value[0]
        return value

    def format_output(self, rendered_widgets, name):
        params = {
            "html_class": self.sub_attrs.get('key', {}).get('class', ''),
            "key": self.key_value,
            "widgets": ''.join(rendered_widgets),
        }
        return (
            """
<li><span class="static_key %(html_class)s">%(key)s</span> :  %(widgets)s</li>
"""
            % params
        )


class EmbeddedFieldWidget(MultiWidget):
    """
    A widget that render each field found in the supplied form.
    """

    def __init__(self, fields, attrs=None):
        self.fields = fields
        super().__init__([f.widget for f in self.fields.values()], attrs)

    def decompress(self, value):
        """
        Retreieve each field value or provide the initial values
        """
        if value:
            return [value.__getitem__(field) for field in self.fields.keys()]
        return [field.field.initial for field in self.fields.values()]

    def format_label(self, field, counter):
        """
        Format the label for each field
        """
        return '<label for="id_formfield_%s" %s>%s:</label>' % (
            counter,
            field.required and 'class="required"',
            field.label,
        )

    def format_help_text(self, field, counter):
        """
        Format the help text for the bound field
        """
        if field.help_text is not None:
            return '(<em>%s</em>)' % field.help_text
        return ''

    def format_output(self, rendered_widgets):
        """
        This output will yeild all widgets grouped in a un-ordered list
        """
        ret = ['<ul class="formfield">']
        for i, field in enumerate(self.fields):
            label = self.format_label(self.fields[field], i)
            help_text = self.format_help_text(self.fields[field], i)
            ret.append('<li>%s %s %s</li>' % (label, help_text, rendered_widgets[i]))

        ret.append('</ul>')
        return ''.join(ret)
