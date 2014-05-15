function deleteServicesCookies() {
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
}

function doLogout() {
    window.qsid = null;
    window.name = null;
    deleteServicesCookies();
    sessionStorage.removeItem("quizqsid");
    sessionStorage.removeItem("quizname");
    sessionStorage.removeItem("quiz_fbid");
    sessionStorage.removeItem("school");
    sessionStorage.removeItem("school_url");
    sessionStorage.removeItem("school_logo_url");
    sessionStorage.removeItem("fbuser_pic");

    var index_url = sessionStorage.getItem('index_url');

    if (index_url === null)
        index_url = "index.html";

    window.location = index_url;
}
