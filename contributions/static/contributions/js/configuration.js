function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

if ( window.history.replaceState ) {
  window.history.replaceState( null, null, window.location.href );
}

$("#tag_selector2").change(function(){
    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    var tag_id = $(this).val();
    $.ajax({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    },
        url: window.location.origin + "/contributions/",
        type: "POST",
        data: {tag:tag_id},
        success: function(data){
            $("#content").html(data)
        }
    });
});