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
        },

        getUrlParameterByName: function(name) {
            name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
            var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
                results = regex.exec(location.search);
            return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
        },

        postJson: function(url, data_or_callback, callback) {
            var payload;
            var func;

            if (typeof data_or_callback == "function") {
                payload = undefined;
                func = data_or_callback;
            }
            else {
                payload = data_or_callback;
                func = callback;
            }

            payload = payload !== undefined ? JSON.stringify(payload): null;
            func = func !== undefined ? func: null;

            return $.ajax({
              url: url,
              type: "POST",
              contentType: "application/json; charset=UTF-8",
              dataType: "json",
              data: payload,
              success: func
            });
        }
    };
}).call(this);
