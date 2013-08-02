function aux_postJSON(url, data, success)
{
  if (success === undefined) {
    $.ajax({
      url: url,
      type: "POST",
      contentType: "application/json; charset=UTF-8",
      dataType: "json",
      success: data
    });
  }
  else {
    $.ajax({
      url: url,
      type: "POST",
      contentType: "application/json; charset=UTF-8",
      data: JSON.stringify(data),
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

function aux_getCookie(Name) {
  var re=new RegExp(Name+"=[^;]+", "i");
  if (document.cookie.match(re))
    return document.cookie.match(re)[0].split("=")[1];    
  return "";
}

function aux_deleteCookie(name, path, domain) {
   if (aux_getCookie(name)) {
     document.cookie = name + "=" + ((path) ? "; path=" + path : "")
     + ((domain) ? "; domain=" + domain : "")
     + "; expires=Thu, 01 Jan 1970 00:00:00 GMT;"
   }
}

function aux_showError(msg) {
  $("#errpopup #errmsg").html("Errore:<br/>" + msg);
  $("#errpopup").popup('open');
}

function updateContentSize() {
  var the_height = ($(window).height()
    - $('[data-role="header"]').height()
    - $('[data-role="footer"]').height())
    - 2 * parseInt($('[data-role="content"]').css("padding-bottom")) - 8;
  $('[data-role="content"]').height(the_height);
  $('[data-role="content"]').width($(window).width()
    - 2 * parseInt($('[data-role="content"]').css("padding-left")));
}
