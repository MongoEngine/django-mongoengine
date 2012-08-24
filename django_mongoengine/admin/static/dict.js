$(document).ready(function(){
	//var dictionaries = new Array();
	var prefixes = new Array();
	var next_pair_ids = new Array();
	var next_dict_ids = new Array();
	var dictionary_ul = $('.dictionary');

	var id;

	dictionary_ul.each(function(index){
		//id = $(this).attr('id');
		var el = $(this);
		save_arrays(el);
		console.log('-----------INIT-----------');
		//console.log('-dict     : '+dictionaries[el.attr('id')]);
		console.log('-prefixes : '+prefixes[el.attr('id')]);
		console.log('-pair id  : '+next_pair_ids[el.attr('id')]);
		console.log('-dict id  : '+next_dict_ids[el.attr('id')]);
		console.log('---------END INIT---------');
	});

	/*
		Save array information
	*/
	function save_arrays(el){
		id = el.attr('id');
		//dictionaries[id] = id;
		prefixes[id] = id.substring(0,id.length-1);
		var next_ids = get_next_ids(el.children('li:last-child').children('input:first-child').attr('id'),prefixes[id]);
		next_pair_ids[id] = next_ids[0];
		next_dict_ids[id] = next_ids[1];
	}

	/*
		Update array information and append HTML
		when pair is added
	*/
	function pair_update_arrays(id){
		el = $('#'+id);
		el.append(get_pair(next_pair_ids[id]));
		i = parseInt(next_pair_ids[id].substring(prefixes[id].length,next_pair_ids[id].length-5)) + 1;
		next_pair_ids[id] = prefixes[id] + i + '_pair_';
		next_dict_ids[id] = prefixes[id] + i + '_subdict_';
	}

	/*
		Update array information and append HTML
		when subdictionary is added
	*/

	//TO VERIFY


	function dict_update_arrays(id){
		el = $('#'+id);
		el.append(get_dict(next_dict_ids[id]));
		var new_id = next_dict_ids[id] + '1_0';
		
		//Event Binding
		$('#add_pair_'+ new_id).click(function(){
			console.log('--------CLICK INNER--------');
			//prefixes[id] = id.substring(0,id.length-1);
			console.log('next_dicts_ids : ' + next_dict_ids[id]);
			prefixes[new_id] = next_dict_ids[id] + '1_'
			pair_update_arrays(new_id);
			console.log('---------END CLICK---------');
		});
		$('#add_sub_'+ new_id).click(function(){
			console.log('--------CLICK INNER--------');
			//prefixes[id] = id.substring(0,id.length-1);
			console.log('next_dicts_ids : ' + next_dict_ids[id]);
			prefixes[new_id] = next_dict_ids[id] + '1_'
			dict_update_arrays(new_id);
			console.log('---------END CLICK---------');
		});

		next_pair_ids[new_id] = prefixes[new_id] + '1_pair_';
		next_dict_ids[new_id] = prefixes[new_id] + '1_subdict_';
	}

	/*
		Get the next ids for the future pair/sub-dictionary,
		for a dictionary referenced by id
	*/
	function get_next_ids(id, prefix){
		console.log('-----------GET NEXT IDS-----------');
		console.log('id     : '+ id);
		console.log('prefix : '+ prefix);
		var n_type = id.substring(prefix.length);

		if ((i = n_type.search('pair')) > 0){
			var first = prefix + (parseInt(n_type.substring(0,i))+1);
			console.log('---------END GET NEXT IDS---------');
			return Array(first+'_pair_',first+'_subdict_');
		}
		else if ((i = n_type.search('subdict')) > 0){
			var first = prefix + (parseInt(u.substring(0,i))+1);
			console.log('---------END GET NEXT IDS---------');
			return Array(first+'_pair_',first+'_subdict_');
		}
		console.log('--------ERROR GET NEXT IDS--------');
	}

	/*
		Get the next HTML element representing a simple pair
	*/
	function get_pair(id){
		console.log('--------GET PAIR-------->');
		console.log('id : '+id);
		return '<li><input type="text" name="'+ id.substring(3) +'0" id="'+ id +'0"/> : '+
			   '<input type="text" name="'+ id.substring(3) +'1" id="'+ id +'1"/></li>';
	}

	/*
		Get the next HTML element representing a sub-dictionary
	*/
	function get_dict(id){
		console.log('--------GET DICT-------->');
		console.log('id : '+id);
		subdict = '<li><input type="text" name="'+ id.substring(3) +'0" id="'+ id +'0"/> : ';
		subdict += '<ul id="'+ id +'1_0" class="dictionary">';
		subdict += '<li><input type="text" name="'+ id.substring(3) +'1_0_pair_0" id="'+ id +'1_0_pair_0"/> : ';
		subdict += '<input type="text" name="'+ id.substring(3) +'1_0_pair_1" id="'+ id +'1_0_pair_1"/></li></ul>';
		subdict += '<span id="add_pair_'+ id +'1_0" class="add_pair_dictionary">Add field</span> -'
		subdict += '<span id="add_sub_'+ id +'1_0" class="add_sub_dictionary">Add subdictionary</span></li>';
		return subdict;
	}

	/*
		Add a field to a dictionary or sub-dictionary
	*/
	$('.add_pair_dictionary').click(function(){
		console.log('-----------CLICK-----------');
		id = $(this).attr('id').substring(4);
		console.log('id : '+id);
		pair_update_arrays(id);
		console.log('---------END CLICK---------');
	});

	/*
		Add a dictionary to a dictionary or sub-dictionary
	*/
	$('.add_sub_dictionary').click(function(){
		console.log('-----------CLICK-----------');
		id = $(this).attr('id').substring(8);
		console.log('id : '+id);
		dict_update_arrays(id);
		console.log('---------END CLICK---------');
	});
});