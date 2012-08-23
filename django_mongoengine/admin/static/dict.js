$(document).ready(function(){
	var dictionaries = new Array();
	var prefixes = new Array();
	var next_els = new Array();
	var dictionary_ul = $('.dictionary');

	dictionary_ul.each(function(index){
		var id = $(this).attr('id');
		dictionaries[id] = $(this);
		prefixes[id] = id.substring(0,id.length-1);
		var next_id = get_next_id($(this).find('li:last-child input:first-child').attr('id'),prefixes[id]);
		next_els[id] = get_next_el(next_id,'pair');
	});

	function get_next_id(id, prefix){
		/*
		Support for default pair dictionaries
		*/
		var u = id.substring(prefix.length);
		/*console.log(id);
		console.log(prefix);
		console.log(u);*/
		if ((i = u.search('pair')) > 0){
			return prefix + (parseInt(u.substring(0,i))+1)+'_pair_';
		}
		console.log('Failed : other type');
	}

	function get_next_el(next_id, type){
		if (type == 'pair'){
			return '<li><input type="text" name="'+ next_id.substring(3) +'0" id="'+ next_id +'0"/> : <input type="text" name="'+ next_id.substring(3) +'1" id="'+ next_id +'1"/></li>';
		}
	}

	$('.add_dictionary').click(function(){
		var id = $(this).attr('id').substring(4);
		dictionaries[id].append(next_els[id]);
		var next_id = get_next_id(dictionaries[id].find('li:last-child input:first-child').attr('id'),prefixes[id]);
		next_els[id] = get_next_el(next_id, 'pair');
	});
});