$("#page-login").bind("pageinit", function() {
  $("#page-login").bind('pageshow', function() {
    aux_busy(false, "#login");
  });

  $.ajaxSetup({cache: false});

$("#loginForm").submit(function (event) {
    event.preventDefault();
    aux_busy(true, "#login");
    console.log(111);
    $.getJSON("/v1/authorize", function(data) {
        var login = $("#login #un").val();
        var passwd = $("#login #pw").val();
        var nonce = data.nonce;
        var digest = hex_md5(login + ':' + passwd);

        var auth = {
          nonce: nonce,
          login: login,
          appid: "32bfe1c505d4a2a042bafd53993f10ece3ccddca",
          'quiz_type': 'b2013',
          digest: hex_md5(nonce + ':' + digest)
        };

        aux_postJSON("/v1/authorize", auth, function (data) {
          if (data.status != 200) {
            aux_busy(false, "#login");
            aux_showError("Nome utente o password non validi.");
          }
          else if (data.user.type != 'student' && data.user.type != 'guest') {
            aux_deleteServicesCookies();
            aux_busy(false, "#login");
            aux_showError("Not a student.");
          }
          else {
            var name = data.user.name;
            if (data.user.surname)
              name += ' ' + data.user.surname;
            window.name = name;
            sessionStorage.setItem('quizname', name);
            sessionStorage.setItem('quizutype', data.user.type);
            $.mobile.changePage("#page-student");
          }
      });
    });
  });
});
