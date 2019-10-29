$(document).ready(function() {
    $('#horizontal-scroll').dataTable( {
        "scrollX": true
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