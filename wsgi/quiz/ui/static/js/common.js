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
        },
        error: function(event) {
            if (event.status == 403 && window.g.user_type == "guest")
                Aux.showGuestError();
        }
    });

    this.Aux = {
        // text must be in form YYYY-MM-DD hh:mm:ss
        // http://stackoverflow.com/questions/15517024/convert-iso-date-string-in-javascript-to-date-object-without-converting-to-loca
        dateFromISOUTC: function(text) {
            var s = text.split(/\D/);
            return new Date(Date.UTC(+s[0], --s[1], +s[2], +s[3], +s[4], +s[5], 0));
        },
        // See dateFromISOUTC()
        strFromISOUTC: function(text) {
            return moment(Aux.dateFromISOUTC(text)).format("LL LT");
        },

        showError: function(msg, callback) {
            // If msg is object then we interested in 'responseJSON'
            // which must be JSON with field 'description'.
            if (msg.responseJSON !== undefined)
                msg = msg.responseJSON.description;
            var dlg = $('#infobox');
            dlg.unbind("hidden.bs.modal");
            if (callback !== undefined)
                dlg.on("hidden.bs.modal", callback);
            dlg.find(".modal-title").html( window.g.labels.error);
            dlg.find('.modal-body').html(msg);
            dlg.modal();
        },

        showInfo: function(msg, callback) {
            var dlg = $('#infobox');
            dlg.unbind("hidden.bs.modal");
            if (callback !== undefined)
                dlg.on("hidden.bs.modal", callback);
            dlg.find(".modal-title").html(window.g.labels.info);
            dlg.find(".modal-body").html(msg);
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
        },

        showGuestError: function() {
            $(".contentpanel #ge-box").show();
        }
    };
}).call(this);