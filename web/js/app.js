/*********************************************************
** AUX tools.
*********************************************************/

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
  //var server = "https://quizplatformtest-editricetoni.rhcloud.com"
  var server = "http://quizplatform-editricetoni.rhcloud.com"
  path = server + url;
  if (window.qsid)
     path += get_arg_prefix(path) + "sid=" + window.qsid;

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
  $.ajax({
    url: url,
    type: "POST",
    contentType: "application/json; charset=UTF-8",
    data: JSON.stringify(data),
    dataType: "json",
    success: success
  });
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



/*********************************************************
** Event handlers.
*********************************************************/

function onAuth(butObj)
{
	butObj.addClass('loading');
	
  $.getJSON(url("/v1/authorize"), function(data) {
  	
    // Calculate digest
    var login = $("#subscribeForm #username").val();
    var passwd = $("#subscribeForm #password").val();
    var nonce = data.nonce;
    var digest = hex_md5(login + ':' + passwd);

    var auth = {
      nonce: nonce,
      login: login,
      appid: "32bfe1c505d4a2a042bafd53993f10ece3ccddca",
      digest: hex_md5(nonce + ':' + digest)
    };

    // Now we can send authorization data
    aux_postJSON(url("/v1/authorize"), auth, function (data) {
      if (data.status != 200) {
        doQuit();
//        aux_showError("Authorization is not passed.", data.status);
		alert("Authorization is not passed." + data.status);
      }
      else {      	
      	var name = data.user.name;
        if (data.user.surname)
          name += ' ' + data.user.surname;
        
        window.qsid = data.sid;
        window.name = name;
//        aux_showFeatures();
		setCookie("qsid", window.qsid, 30)
		setCookie("name", window.name, 30)
		window.location = "menu.html";
      }
    });
  }); // GET
  
//  alert('ed');
}
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
});
