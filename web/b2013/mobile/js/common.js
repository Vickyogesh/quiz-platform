if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) { 
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}

function getUrlParameterByName(name) {
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}

function aux_postJSON(url, data, success)
{
  if (success === undefined) {
    return $.ajax({
      url: url,
      type: "POST",
      contentType: "application/json; charset=UTF-8",
      dataType: "json",
      success: data
    });
  }
  else {
    return $.ajax({
      url: url,
      type: "POST",
      contentType: "application/json; charset=UTF-8",
      data: data != null ? JSON.stringify(data) : null,
      dataType: "json",
      success: success
    });
  }
}

function aux_busy(state, forWidget) {
  if (state) {
    $.mobile.loading('show');
    if (forWidget !== undefined)
      $(forWidget).addClass("ui-disabled");
  }
  else {
    $.mobile.loading('hide');
    if (forWidget !== undefined)
      $(forWidget).removeClass("ui-disabled");
  }
}

function aux_deleteServicesCookies() {
    function deleteCookie(name, path, domain) {
        var i = name.indexOf('=');
        if (i != -1)
            name = name.substring(0, i);

        if (name) {
            document.cookie = name + "=" +
                ((path) ? "; path=" + path : "") +
                ((domain) ? "; domain=" + domain : "") +
                "; expires=Thu, 01 Jan 1970 00:00:00 GMT;"
        }
    }

    if (!String.prototype.trim) {
        String.prototype.trim = function() {
            return this.replace(/^\s+|\s+$/g, '');
        };
    }

    var theCookies = document.cookie.split(';');

    for (var i = 0; i <theCookies.length; i++) {
        var c = theCookies[i].trim();
        if (c.substring(0, 3) == 'tw_')
        deleteCookie(c, '/');
    }
    sessionStorage.removeItem('quiz_fbid');
    sessionStorage.removeItem("fbuser_pic");
}

function aux_showError(msg, title) {
  $(document).simpledialog2({
    mode: 'blank',
    headerText: (title === undefined ? "Errore" : title),
    headerClose: false,
    blankContent : 
      "<p>" + msg + "</p>" +
      "<a rel='close' data-role='button' href='#'>Close</a>"
  });
}

function aux_logout() {
    window.name = null;
    aux_busy(true);
    $.ajax("/v1/authorize/logout").always(function() {
        aux_deleteServicesCookies();
        aux_busy(false);
        $.mobile.changePage("#page-login");
    });
}

function aux_layoutGrid(id) {
    var p = $(id).parent();
    var pw = p.width();
    var ph = p.height();
    var grid = $(id);

    if (pw >= ph) { // horizontal
        grid.addClass("ftable ui-grid-b");
        grid.removeClass("ui-grid-solo");

        $(id + " > div").each(function(index){
            if (index == 0)
              $(this).addClass("item");
            else {
                $(this).addClass("item ui-block-" + String.fromCharCode(97 + index));
                $(this).removeClass("ui-block-a");
            }
        });
    }
    else {
        grid.addClass("ui-grid-solo");
        grid.removeClass("ftable ui-grid-b");

        $(id + " > div").each(function(index){
            if (index == 0)
              $(this).removeClass("item");
            else {
                $(this).addClass("ui-block-a");
                $(this).removeClass("item ui-block-" + String.fromCharCode(97 + index));
            }
        });
    }
}
