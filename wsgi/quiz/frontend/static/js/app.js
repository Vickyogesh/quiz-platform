$.ajaxSetup({cache: false});

/*********************************************************
** AUX tools.
*********************************************************/

function aux_getCookie(name) {
  var matches = document.cookie.match(new RegExp(
    "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
  ));
  return matches ? decodeURIComponent(matches[1]) : undefined;
}

function getUrlParameterByName(name) {
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}

// 100% errors = gray pie
// 0% errors =  blue pie
// null or -1 = white pie
// showEmpty - show white pie if error_percent is null or -1
function createErrorsChart(id, error_percent, showEmpty) {
  var p = Raphael(id);
  var values;
  var colors;
  var stroke = "#FFF"

  if (error_percent == 0) {
    error_percentues = [100];
    colors = ['#FFF'];
  }
  else if (error_percent == 100) {
    error_percentues = [100];
    colors = ['#FFF'];
  }
  else if (error_percent > 0 ) {
    error_percentues = [100 - error_percent, error_percent];
    colors = ['#2479cc', '#FFF'];
  }
  else {
    error_percent = -1;
    if (showEmpty) {
      error_percentues = [100];
      colors= ["#FFF"];
      stroke = "#CCC";
    }
    else {
      error_percentues = [];
      colors= [];
    }
  }

  p = p.piechart(10, 10, 8, error_percentues, {
    stroke: stroke,
    strokewidth: 2,
    colors: colors
  });

  if (error_percent == 0)
    p.series.items[0].attr({opacity : 100, fill: "#2479CC"});
  else if (error_percent == 100)
    p.series.items[0].attr({opacity : 100, fill: "#CCC"});
  else if (error_percent > 0)
    p.series.items[1].attr({opacity : 100, fill: "#CCC"});

  return p;
}
//----------------------------------------------------------------------------

function get_arg_prefix(url)
{
    if (url.indexOf('?') == -1)
      return "?";
    else
      return "&";
}
//----------------------------------------------------------------------------

function url(url)
{
  var path = url;

  // NOTE: uncomment if you want cross domain requests
  //var server = "http://127.0.0.1"
  // var server = "http://quizplatform-editricetoni.rhcloud.com"
  // path = server + url;
  // if (window.qsid)
  //    path += get_arg_prefix(path) + "sid=" + window.qsid;

  return path;
}
//---------------------------------------------------------------------------

// Remove session cookie, hide features and show login dialog
function doQuit()
{
  window.qsid = null;
//  aux_showLogin();
	$('.cssSubmitButton').removeClass('loading');

}
//----------------------------------------------------------------------------

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
      data: null ? JSON.stringify(data): null,
      dataType: "json",
      success: success
    });
  }
}
//----------------------------------------------------------------------------

function aux_showJSONError(data)
{
  if (data.responseText !== undefined)
    data = JSON.parse(data.responseText);
  aux_showError(data.description, data.status)
}
//----------------------------------------------------------------------------

// Show error dialog
function aux_showError(msg, code)
{
  if (code !== undefined)
    alert('Errore: ' + code + ', ' + msg);
  else
    alert('Errore: ' + msg);
}
//----------------------------------------------------------------------------

function showGuestAccessError() {
  alert("Guest's visits is exceeded. Access will be unlocked within 1 hr.");
  if (window.back_url !== undefined)
    window.location = window.back_url;
}
//----------------------------------------------------------------------------

$(document).ready(function() {
	var nwidth = $(window).width();

	if (nwidth >= 950)
		$('#work_area').addClass('workareanormal');
	else
		$('#work_area').addClass('workareareduced');
		
	$('#btnlogout').click(function(){
		window.qsid = null;
		window.location = "/";
	});
});
