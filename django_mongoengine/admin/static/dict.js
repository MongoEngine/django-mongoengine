$(document).ready(function(){
	var dictionaries = new Array();
	var prefixes = new Array();
	var next_els = new Array();
	var dictionary_ul = $('.dictionary');

	dictionary_ul.each(function(index){
		var id = $(this).attr('id');
		dictionaries[id] = $(this);
		prefixes[id] = id.substring(0,id.length-1);
		var next_id = get_next_id($(this).children('li:last-child').children('input:first-child').attr('id'),prefixes[id]);
		next_els[id] = get_next_el(next_id,'pair');
	});
	console.log('global > ');
	console.log(dictionary_ul);
	function get_next_id(id, prefix){
		console.log('get_next_id > Entering : '+ id + ', ' + prefix)
		var u = id.substring(prefix.length);
		/*console.log(id);
		console.log(prefix);
		console.log(u);*/
		if ((i = u.search('pair')) > 0){
			return prefix + (parseInt(u.substring(0,i))+1)+'_pair_';
		}
		else if ((i = u.search('subdict')) > 0){
			return prefix + (parseInt(u.substring(0,i))+1)+'_pair_';
		}
		console.log('get_next_id > Passed trough : '+ id + ', ' + prefix)
		//console.log(id);
		//console.log(prefix);
	}

	function get_next_el(next_id, type){
		console.log('get_next_el > ' + next_id);
		if (type == 'pair'){
			return '<li><input type="text" name="'+ next_id.substring(3) +'0" id="'+ next_id +'0"/> : <input type="text" name="'+ next_id.substring(3) +'1" id="'+ next_id +'1"/></li>';
		}
	}

	/*
	Add a field to a dictionary or subdictionary
	*/

	$('.add_dictionary').click(function(){
		var id = $(this).attr('id').substring(4);
		console.log('click_function > '+ id);
		dictionaries[id].append(next_els[id]);
		var next_id = get_next_id(dictionaries[id].find('li:last-child input:first-child').attr('id'),prefixes[id]);
		if ((next_el = get_next_el(next_id, 'pair')) == next_els[id]){
			console.log('click_function > SAME ELS');
			console.log('click_function > ' + dictionaries[id].children('li:last-child').children('input:first-child').attr('id'));
		}
		else {
			next_els[id] = next_el;
		}
	});

	/*
	Add a subdictionary to a dictionary or subdictionary
	*/

	$('.add_sub_dictionary').click(function(){
		var id = $(this).attr('id').substring(8);
		
	});
});