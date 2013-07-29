$(document).ready(function(){

    /*----------------------------------------------------------------------*/
    var DEBUG = false;

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
        Transform full read-only dictionaries in text
    ************************************************************************/

    var readonly_dicts = $('p:contains({)');
    debug(readonly_dicts);
    readonly_dicts.each(function(){
        var text = $(this).text();
        text = text.replace(/u'/g, '');
        text = text.replace(/'/g, '');
        $(this).html(get_html(text));
    });

    function get_html(text){
        debug('------ENTERING get_html');
        var html = '<ul>';
        var pairs = get_pairs(text);
        debug(pairs);
        for (var i = 0; i < pairs.length; i++){
            if (pairs[i][1].contains('{')){
                html += '<li>' + pairs[i][0] + ': ' + get_html(pairs[i][1]) + '</li>';
            }
            else {
                html += '<li>' + pairs[i][0] + ': ' + pairs[i][1] + '</li>';
            }
        }
        return html + '</ul>';
    }

    function get_pairs(text){
        text = text.slice(1,-1);
        //checker si indexOf({) existe et est plus petit que indexOf(,),
        //si oui, on ne fait rien sur le premier et on passe au 2e ? comment ?
        var pairs = text.split(', ', 1);
        for (var i = 0; i < pairs.length; i++){
                pairs[i] = pairs[i].split(': ');
        }
        debug('------PAIRS : ');
        debug(pairs);
        return pairs;
    }

    function debug(text) {
        if (DEBUG) {
            console.log(text)
        }
    }
});