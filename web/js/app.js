/*********************************************************
** AUX tools.
*********************************************************/


function createErrorsChart(id, val) {
  var p = Raphael(id);
  p = p.piechart(10, 10, 8, [100 - val, val], {
    stroke:'#fff',
    strokewidth:2,
    colors:['#2479cc','#fff']
  });

  // $(p.series.items[0].node).attr("id", "i0");
  // $(p.series.items[1].node).attr("id", "i1");
  p.series.items[1].attr({opacity : 100, fill: "#ccc"});
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
//----------------------------------------------------------------------------

function aux_showJSONError(data)
{
  aux_showError(data.description, data.status)
}
//----------------------------------------------------------------------------

// Show error dialog
function aux_showError(msg, code)
{
//  $("#msg .modal-header h3").html('Error: ' + code);
//  $("#msg .modal-body").html(msg)
//  $("#msg").modal('show')
	alert('Error: ' + code + ', ' + msg);
}
//----------------------------------------------------------------------------



//----------------------------------------------------------------------------
/*
function onGetQuiz(nTopicVal)
{
//  $("#quiztab table thead input").attr("checked", false);

//	var topic = $("#quiztab #topic").val();
//  var lang = $("#quiztab #lang").val();
	var lang = "it";
	var uri = url("/v1/quiz/" + nTopicVal);
	var data = {}
	
	alert(uri);
	
	if (lang != "it")
		data.lang = lang;
	
	$.getJSON(uri, data, function(data) {
		if (data.status != 200) {
			aux_showJSONError(data);
		}
		else {
			alert('success: ' + data);
			aux_fillTable($("#quiztab table"), data.questions);
		}
	});
}
//----------------------------------------------------------------------------
*/

$(document).ready(function() {
	var nwidth = $(window).width();

	if (nwidth >= 950)
		$('#work_area').addClass('workareanormal');
	else
		$('#work_area').addClass('workareareduced');
		
	$('#btnlogout').click(function(){
		window.qsid = null;
		window.location = "index.html";
	});
});
