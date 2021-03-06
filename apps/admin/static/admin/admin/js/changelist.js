
jQuery(function(){

    check_up_count_selected_objects = function check_up_count_selected_objects (){
        var count_selected = $('#changelist table tbody td input[type="checkbox"]:checked').length;
        $('#count_selected_objects').text(count_selected);
    }

    /*
    Check/uncheck all rows in table
     */
    $('#changelist table thead th:first-child input[type="checkbox"]').bind('click', function(event) {

        var $rows_checkboxes = $('#changelist table tbody td:first-child input[type="checkbox"]');

        var now_is_checked = $(this).is(':checked');

        if (now_is_checked === true){
            $rows_checkboxes.prop("checked", true);
        } else {
            $rows_checkboxes.prop("checked", false);
        }

        check_up_count_selected_objects()

    });

    /*

    */
   $('#changelist table tbody td input[type="checkbox"]').bind('change', function(e){
        check_up_count_selected_objects();
    });

   $('table thead th.is_sortable').bind('click', function(e){

        var value_clicked_column = $(this).find('input[type="hidden"]').val();
        var object = JSON.parse(value_clicked_column);

        var name_clicked_column = Object.keys(object)[0];

        var $form = $(this).parents('form');

        var $hidden_input = $('<input />').
          attr('name', '__clickedColumn').
          attr('value', name_clicked_column).
          attr('type', 'hidden');
        $form.append($hidden_input);

        var $hidden_input = $('<input />').
          attr('name', '__discardSorting').
          attr('value', false).
          attr('type', 'hidden');
        $form.append($hidden_input);

        $form.submit();
   });

   /*
   Toggle right sidebar with filters
   */
   $('#btn_hide_filters,#btn_show_filters').bind('click', function(e){
       $('#display_filters').toggleClass('hidden');
       $('#hidden_filters').toggleClass('hidden');
   });

   var $table_search_details = $('#table_search_details');
   $('#toggle_search_details').bind({
       click: function(e){
           $table_search_details.stop().fadeToggle(500);
       },
   });

   /*

    */
   $('select#list_display').bind({
        change: function(){
            $(this).parents('form').submit();
        },
    });

   /*
   */
   $('td.discard_ordering_column').bind({
    click: function(e){

      e.stopPropagation();
      e.preventDefault();

      var value_clicked_column = $(this).parent().find('input[type="hidden"]').val();
      var object = JSON.parse(value_clicked_column);

        var name_clicked_column = Object.keys(object)[0];

        var $form = $(this).parents('form');

        var $hidden_input = $('<input />').
          attr('name', '__clickedColumn').
          attr('value', name_clicked_column).
          attr('type', 'hidden');
        $form.append($hidden_input);

        var $hidden_input = $('<input />').
          attr('name', '__discardSorting').
          attr('value', true).
          attr('type', 'hidden');
        $form.append($hidden_input);

        $form.submit();

    },
   });

});
