(function() {
    // NOTE: busy element id is hardcoded.
    var busy_el_id = "#busy_layer";

    $.ajaxSetup({
        cache: false,
        // Show busy indicator before sending request.
        beforeSend: function() {
            $(busy_el_id).fadeIn(100);
        },
        // Hide busy indicator after sending request.
        complete: function() {
            $(busy_el_id).fadeOut();
        }
    });

    this.Aux = {
        showError: function(msg) {
            // If msg is object then we interested in 'responseJSON'
            // which must be JSON with field 'description'.
            if (msg.responseJSON !== undefined)
                msg = msg.responseJSON.description;
            var dlg = $('#errorbox');
            dlg.find('.modal-body').html(msg);
            dlg.modal();
        }
    };
})();
