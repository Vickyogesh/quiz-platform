$.getScript('//connect.facebook.net/en_UK/all.js', function() {
    FB.init({
        appId: '306969962800273',
        version: "v2.0",
        status: true,
        xfbml: 1
    });
});

function do_auth(data) {
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

        $.mobile.changePage("#page-student");
    }
}

$("#page-login").bind("pageinit", function() {
    $.ajaxSetup({cache: false});

    $("#page-login").bind('pageshow', function() {
        aux_busy(false, "#login");
        $("#page-student #fbpic").attr('src', '');
        $("#page-student #fbpic").hide();
    });


    $("#loginForm").submit(function (event) {
        event.preventDefault();
        aux_busy(true, "#login");
        $.getJSON(url("/v1/authorize")).always(function(data) {
            data = JSON.parse(data.responseText);
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

            aux_postJSON(url("/v1/authorize"), auth, null).always(do_auth);
        });
    });
});
