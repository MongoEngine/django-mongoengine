from django.forms.widgets import TextInput, MultiWidget
from django.utils.safestring import mark_safe

import pdb

class Dictionary(MultiWidget):
	"""
	A widget representing a dictionary field
	"""

	def __init__(self, keys, min_length, attrs=None):
		#pdb.set_trace()
		#have a politic here : if widgets, then check if value pairing name/value
		# if no widget, only one row to begin (or if attribute min_length ?)
		widget_object = []
		if keys:
			for k in keys:
				widget_object.append(Pair(key=k,attrs=attrs))
		else:
			for i in range(min_length):
				widget_object.append(Pair(attrs=attrs))
		self.attrs = attrs
		super(Dictionary, self).__init__(widget_object,attrs)

	#TODO implement the render method : take a dict as value and display a list of inputs ?
	#	  check that WHERE the dict is passed
	#TODO implement the value_from_datadict method if needed : it gets data from POST
	#TODO : get the value from the different widgets with decompress
	def decompress(self, value):
		return [value[name] for name in self.widgets_names]

	def render(self, name, value, attrs=None):
		#pdb.set_trace()
		if self.is_localized:
			for widget in self.widgets:
				widget.is_localized = self.is_localized
		if not isinstance(value,list):
			value = self.decompress(value)
		output = []
		final_attrs = self.build_attrs(attrs)
		id_ = final_attrs.get('id',None)
		for i, widget in enumerate(self.widgets):
			try:
				widget_value = value[i]
			except IndexError:
				widget_value = None
			if id_:
				final_attrs = dict(final_attrs, id='%s_%s' % (id_, self.widgets_names[i]))
			output.append(widget.render(name + '_%s' % self.widgets_names[i], widget_value, final_attrs))
		return mark_safe(self.format_output(output))

	def value_from_datadict(self, data, files, name):
		return [widget.value_from_datadict(data, files, name + '_%s' % self.widgets_names[i]) for i, widget in enumerate(self.widgets)]

	def format_output(self, rendered_widgets):
		#pdb.set_trace()
		format = '<div>'
		for i, rendered_widget in enumerate(rendered_widgets):
			format += '<div><br/><label>%s</label>' % self.widgets_names[i] + rendered_widget + '</div>'
		return format+'</div>'
