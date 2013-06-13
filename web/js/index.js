$(document).ready(function () {
	
	$(document).ajaxError(function() {
		alert('Unexpected server response.');
		
		$('.cssSubmitButton').removeClass('loading');
	});
	
	doQuit();
    
    $('#button a').click(function () {
        
		var link = $(this);
		onAuth(link);
	});
	
	$('input').css('border','0px');
        
});

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
		sessionStorage.setItem('quizqsid', window.qsid);
    sessionStorage.setItem('quizname', window.name);
    sessionStorage.setItem('quizutype', data.user.type);

		if (data.user.type == 'student')
			window.location = "student.html";
		else if (data.user.type == 'school')
			window.location = "School.html";
      }
    });
  }); // GET
  
//  alert('ed');
}
