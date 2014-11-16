$(document).ready(function () {
	$(document).ajaxError(function() {
		$('.cssSubmitButton').removeClass('loading');
	});
	
	doQuit();

  $("#subscribeForm").submit(function (event) {
    event.preventDefault();
		var link = $("#subscribeForm .cssSubmitButton");
		onAuth(link);
	});
	
	$('input').css('border','0px');

  $.getScript('//connect.facebook.net/it_IT/sdk.js', function() {
    FB.init({
        appId: '306969962800273',
        version: "v2.0",
        xfbml: true,
        status: true
    });

    var fblogin = getUrlParameterByName("fblogin");
    if (fblogin == "1") {
      WaitMsg.show();
      FB.getLoginStatus(function(response) {
        if (response.status !== 'connected') {
          WaitMsg.hide();
          console.log('Collegamento non riuscito!');
        }
        else {
          var auth = {
            fb: {
              id: response.authResponse.userID,
              token: response.authResponse.accessToken
            },
            appid: "32bfe1c505d4a2a042bafd53993f10ece3ccddca",
            'quiz_type': 'b2013'
          };

          WaitMsg.show();
          aux_postJSON(url("/v1/authorize"), auth, null).always(do_auth);
        }
      });
    }
  });
});

/*********************************************************
** Event handlers.
*********************************************************/

function onAuth(butObj)
{
	butObj.addClass('loading');
	
  $.getJSON(url("/v1/authorize")).always(function(data) {	
    data = JSON.parse(data.responseText);
    // Calculate digest
    var login = $("#subscribeForm #username").val();
    var passwd = $("#subscribeForm #password").val();
    var nonce = data.nonce;
    var digest = hex_md5(login + ':' + passwd);

    var auth = {
      nonce: nonce,
      login: login,
      appid: "32bfe1c505d4a2a042bafd53993f10ece3ccddca",
      'quiz_type': 'b2013',
      digest: hex_md5(nonce + ':' + digest)
    };

    // Now we can send authorization data
    WaitMsg.show();
    aux_postJSON(url("/v1/authorize"), auth, null).always(do_auth);
  }); // GET
  
//  alert('ed');
}

function onFbLogin() {
  FB.getLoginStatus(function(response) {
    if (response.status !== 'connected') {
      //Facebook account is not linked
      alert('Collegamento non riuscito!');
    }
    else {
      var auth = {
        fb: {
          id: response.authResponse.userID,
          token: response.authResponse.accessToken
        },
        appid: "32bfe1c505d4a2a042bafd53993f10ece3ccddca",
        'quiz_type': 'b2013'
      };

      WaitMsg.show();
      aux_postJSON(url("/v1/authorize"), auth, null).always(do_auth);
    }
  });
}

function do_auth(data) {
  WaitMsg.hide();
  if (data.status != 200) {
    doQuit();
    var fblogin = getUrlParameterByName("fblogin");
    if (fblogin != "1")
      alert("Nome utente o password non validi.");
  }
  else {        
    var name = data.user.name;
    if (data.user.surname)
      name += ' ' + data.user.surname;
    
    window.qsid = data.sid;
    window.name = name;
    sessionStorage.setItem('quizqsid', window.qsid);
    sessionStorage.setItem('quizname', window.name);
    sessionStorage.setItem('quizutype', data.user.type);
    if (data.user.fb_id !== undefined && data.user.fb_id !== null)
      sessionStorage.setItem('quiz_fbid', data.user.fb_id);
    else
      sessionStorage.removeItem("quiz_fbid");

    var school = getUrlParameterByName("n");
    var school_url = getUrlParameterByName("nu");
    var school_logo_url = getUrlParameterByName("nl");
    sessionStorage.setItem('school', school);
    sessionStorage.setItem('school_url', school_url);
    sessionStorage.setItem('school_logo_url', school_logo_url);
    sessionStorage.setItem('index_url', window.location.href);

    if (data.user.type == 'student' || data.user.type == 'guest')
      window.location = "student.html";
    else if (data.user.type == 'school') {
      sessionStorage.setItem('quizname_school', window.name);
      window.location = "School.html";
    }
    else if (data.user.type == 'admin')
      window.location = "admin.html";
  }
}
