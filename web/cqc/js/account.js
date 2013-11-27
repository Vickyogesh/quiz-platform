function editAccount(student_id) {
    var loc = window.location

    var search = loc.search;
    if (search.indexOf("upd=1") == -1) {
        if (search == "")
            search += "?";
        else
            search += "&";
        search += "upd=1";
    }

    var path = loc.protocol + "//" + loc.host + loc.pathname + search
    var param = "?next=" + encodeURIComponent(path);

    if (student_id != undefined)
        param += "&uid=" + student_id;

    window.location = url("/v1/accounturl") + param;
}
