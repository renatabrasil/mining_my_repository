$(document).ready(function() {
//    $('#horizontal-scroll').dataTable( {
//        "scrollX": true
//    } );

    // Setup - add a text input to each footer cell
    $('#example tfoot th').each( function () {
        var title = $(this).text();
        $(this).html( '<input type="text" placeholder="Search '+title+'" />' );
    } );

    // DataTable
//    var table = $('#example').DataTable();
    $('#example').dataTable( {
      "pageLength": 50
    } );
    // Apply the search
    table.columns().every( function () {
        var that = this;

        $( 'input', this.footer() ).on( 'keyup change clear', function () {
            if ( that.search() !== this.value ) {
                that
                    .search( this.value )
                    .draw();
            }
        } );
    } );
} );

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

if ( window.history.replaceState ) {
  window.history.replaceState( null, null, window.location.href );
}

$("#update-direc2tory").submit(function(){
    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    var tag_id = $(this).val();
    $.ajax({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    },
        url: $(this).attr("action"),
        type: "PUT",
        data: {directory_id:directory_id},
        success: function(data){
            $("#content").html(data)
        }
    });
});