$(document).ready(function(){

    /*----------------------------------------------------------------------*/
    var DEBUG = true;

    function print_array(a,name){
        debug('--------------------');
        if ($.isArray(a)){
            for (var key in a){
                if (key === 'length' || !a.hasOwnProperty(key)) continue;
                debug(name+'['+key+'] = '+a[key]);
            }
        }
    }
    /*----------------------------------------------------------------------*/

    /************************************************************************
        Those array are useful to keep track of the different ids
    ************************************************************************/

    var prefixes = [];
    var next_pair_ids = [];
    var next_dict_ids = [];
    var dictionary_ul = $('.dictionary');
    var depths = [];
    var id;

    /************************************************************************
        Initialization
    ************************************************************************/

    dictionary_ul.each(function(index){
        debug('-----------INIT-----------');
        var el = $(this);
        save_arrays(el);
        debug('---------END INIT---------');
    });

    $('.del_pair').each(function(){
        hide_delete(this);
    });

    $('.del_dict').each(function(){
        hide_delete(this);
    });

    print_array(prefixes,'prefixes');
    print_array(next_pair_ids,'pairs ids');
    print_array(next_dict_ids,'dict ids');
    print_array(depths,'depths');

    /************************************************************************
        Save array information
    ************************************************************************/

    function save_arrays(el){
        var id = el.attr('id');
        debug(id);
        prefixes[id] = id.substring(0,id.length-1);
        var next_ids = get_next_ids(el.children('li:last-child').children('input:first-child').attr('id'),prefixes[id]);
        next_pair_ids[id] = next_ids[0];
        next_dict_ids[id] = next_ids[1];
        var cl = el.attr('class');
        var i;
        if ((i = cl.indexOf('depth_')) != -1){
            depths[id] = cl.substring(i+6);
            if (depths[id] == '0'){
                debug('depth equal to zero');
                $('.add_sub_dictionary').remove();
            }
        }
        else{
            depths[id] = -1;
        }
    }

    /************************************************************************
        Hiding the Delete buttons where dictionaries
        only have one child
    ************************************************************************/

    function hide_delete(el){
        var id = 'id' + $(el).attr('id').substring(3) + '_0';
        var parent = $("ul:has(>li >#"+id+")");

        if (parent.children("li").size() == 1){
            debug('---------NO DEL---------');
            $(el).hide();
        }
    }

    /************************************************************************
        Get the next HTML element representing a simple pair
    ************************************************************************/

    function get_pair(id){
        debug('--------GET PAIR-------->');
        debug('id : '+id);
        return '<li><input type="text" name="'+ id.substring(3) +'0" id="'+ id +'0"/> : '+
               '<input type="text" name="'+ id.substring(3) +'1" id="'+ id +'1"/>'+
               '<span class="del_pair" id="del_'+ id.substring(3,id.length-1) +'"> - Delete</span></li>';
    }

    /************************************************************************
        Get the next HTML element representing a sub-dictionary
    ************************************************************************/

    function get_dict(id, parent){
        debug('--------GET DICT-------->');
        debug('id : '+id);
        debug('depth : '+ depths[parent]);
        this_depth = id.match(/subdict/igm);
        this_depth = (this_depth) ? this_depth.length : 0;
        class_depth = (depths[parent] != -1) ? 'depth_' + depths[parent] : '';

        subdict = '<li><input type="text" name="'+ id.substring(3) +'0" id="'+ id +'0"/> : ';
        subdict += '<ul id="'+ id +'1_0" class="dictionary '+ class_depth +'">';
        subdict += '<li><input type="text" name="'+ id.substring(3) +'1_0_pair_0" id="'+ id +'1_0_pair_0"/> : ';
        subdict += '<input type="text" name="'+ id.substring(3) +'1_0_pair_1" id="'+ id +'1_0_pair_1"/>';
        subdict += '<span class="del_pair" id="del_'+ id.substring(3) +'1_0_pair"> - Delete</span></li></ul>';
        subdict += '<span id="add_pair_'+ id +'1_0" class="add_pair_dictionary">Add field</span>';
        if (this_depth < depths[parent]){
            subdict += '<span id="add_sub_'+ id +'1_0" class="add_sub_dictionary"> - Add subdictionary</span>';
        }
        subdict += '<span class="del_dict" id="del_'+ id.substring(3,id.length-1) +'"> - Delete</span></li>';
        return subdict;
    }

    /************************************************************************
        Update array information and append HTML
        when pair is added
    ************************************************************************/

    function pair_update_arrays(id){
        var el, i, del_pair_button;
        debug('--------PAIR UPDATE--------');
        print_array(prefixes,'prefixes');
        print_array(next_pair_ids,'pairs ids');
        print_array(next_dict_ids,'dict ids');
        el = $('#'+id);
        el.append(get_pair(next_pair_ids[id]));
        del_pair_button = $('#del_'+ next_pair_ids[id].substring(3,next_pair_ids[id].length-1));
        el.children('li').children('.del_pair').show();
        el.children('li').children('.del_dict').show();
        i = parseInt(next_pair_ids[id].substring(prefixes[id].length,next_pair_ids[id].length-5),10) + 1;
        debug('i = '+i);
        next_pair_ids[id] = prefixes[id] + i + '_pair_';
        next_dict_ids[id] = prefixes[id] + i + '_subdict_';
        print_array(prefixes,'prefixes');
        print_array(next_pair_ids,'pairs ids');
        print_array(next_dict_ids,'dict ids');

        //Event Binding
        del_pair_button.click(function(){
            debug('---------DEL INNER---------');
            var id = 'id' + $(this).attr('id').substring(3) + '_0';
            delete_row(id,'pair');
        });
    }

    /************************************************************************
        Update array information and append HTML
        when subdictionary is added
    ************************************************************************/

    function dict_update_arrays(id){
        var el, i, del_pair_button, del_dict_button, new_id;
        debug('--------DICT UPDATE--------');
        el = $('#'+id);
        el.append(get_dict(next_dict_ids[id], id));
        del_pair_button = $('#del_'+ next_dict_ids[id].substring(3) +'1_0_pair');
        del_dict_button = $('#del_'+ next_dict_ids[id].substring(3, next_dict_ids[id].length-1));
        el.children('li').children('.del_pair').show();
        el.children('li').children('.del_dict').show();
        debug(del_pair_button);
        debug(del_dict_button);
        i = parseInt(next_dict_ids[id].substring(prefixes[id].length,next_dict_ids[id].length-8), 10) + 1;
        debug('i = '+i);

        new_id = next_dict_ids[id] + '1_0';

        prefixes[new_id] = next_dict_ids[id] + '1_';
        next_pair_ids[new_id] = prefixes[new_id] + '1_pair_';
        next_dict_ids[new_id] = prefixes[new_id] + '1_subdict_';
        depths[new_id] = depths[id];

        print_array(prefixes,'prefixes');
        print_array(next_pair_ids,'pairs ids');
        print_array(next_dict_ids,'dict ids');

        //Event Binding
        $('#add_pair_'+ new_id).click(function(){
            debug('--------CLICK INNER--------');
            pair_update_arrays(new_id);
            debug('---------END CLICK---------');
        });
        $('#add_sub_'+ new_id).click(function(){
            debug('--------CLICK INNER--------');
            dict_update_arrays(new_id);
            debug('---------END CLICK---------');
        });

        $(del_pair_button).click(function(){
            var id = 'id' + $(this).attr('id').substring(3) + '_0';
            delete_row(id,'pair');
        });

        $(del_dict_button).click(function(){
            var id = 'id' + $(this).attr('id').substring(3) + '_0';
            delete_row(id,'dict');
        });

        //hide the del_pair button as there is only one row
        $(del_pair_button).hide();

        next_pair_ids[id] = prefixes[id] + i + '_pair_';
        next_dict_ids[id] = prefixes[id] + i + '_subdict_';
    }

    /************************************************************************
        Get the next ids for the future pair/sub-dictionary,
        for a dictionary referenced by id
    ************************************************************************/

    function get_next_ids(id, prefix){
        debug('-----------GET NEXT IDS-----------');
        debug('id     : '+ id);
        debug('prefix : '+ prefix);
        var n_type = id.substring(prefix.length);
        var first;

        if ((i = n_type.search('pair')) > 0){
            first = prefix + (parseInt(n_type.substring(0,i), 10)+1);
            debug('---------END GET NEXT IDS---------');
            return Array(first+'_pair_',first+'_subdict_');
        }
        else if ((i = n_type.search('subdict')) > 0){
            first = prefix + (parseInt(n_type.substring(0,i), 10)+1);
            debug('---------END GET NEXT IDS---------');
            return Array(first+'_pair_',first+'_subdict_');
        }
        debug('--------ERROR GET NEXT IDS--------');
        return '';
    }

    /************************************************************************
        Add a field to a dictionary or sub-dictionary
    ************************************************************************/

    $('.add_pair_dictionary').click(function(){
        debug('-----------CLICK-----------');
        id = $(this).attr('id').substring(4);
        debug('id : '+id);
        pair_update_arrays(id);
        debug('---------END CLICK---------');
    });

    /************************************************************************
        Add a dictionary to a dictionary or sub-dictionary
    ************************************************************************/

    $('.add_sub_dictionary').click(function(){
        debug('-----------CLICK-----------');
        id = $(this).attr('id').substring(8);
        debug('id : '+id);
        dict_update_arrays(id);
        debug('---------END CLICK---------');
    });

    /************************************************************************
        Delete a row, according to its type
    ************************************************************************/

    function delete_row(id){
        debug('---------DEL CLICK---------');
        var parent = $("ul:has(>li >#"+id+")");
        var parent_id = parent.attr('id');

        debug('id :' + id);
        debug('parent id :' + parent_id);
        if (parent.children("li").size() > 1){
            $("li:has(>#"+ id +")").remove();

            var next_ids = get_next_ids(parent.children('li:last-child').children('input:first-child').attr('id'),prefixes[parent_id]);
            next_pair_ids[parent_id] = next_ids[0];
            next_dict_ids[parent_id] = next_ids[1];
        }

        if (parent.children("li").size() == 1){
            debug('---------NO DEL---------');
            parent.children('li').children('.del_pair').hide();
            parent.children('li').children('.del_dict').hide();
        }
    }

    /************************************************************************
        Delete a pair
    ************************************************************************/

    $('.del_pair').click(function(){
        debug('---------DEL CLICK---------');
        id = 'id' + $(this).attr('id').substring(3) + '_0';
        delete_row(id);

        print_array(prefixes,'prefixes');
        print_array(next_pair_ids,'pairs ids');
        print_array(next_dict_ids,'dict ids');
    });

    /************************************************************************
        Delete a sub-dictionary
    ************************************************************************/

    $('.del_dict').click(function(){
        debug('-------DEL CLICK DICT-------');
        id = 'id' + $(this).attr('id').substring(3) + '_0';
        delete_row(id);

        print_array(prefixes,'prefixes');
        print_array(next_pair_ids,'pairs ids');
        print_array(next_dict_ids,'dict ids');
    });

    function debug(text) {
        if (DEBUG) {
            console.log(text);
        }
    }
});
