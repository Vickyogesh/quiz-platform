function editAccount(student_id) {
    var loc = window.location
    var path = loc.protocol + "//" + loc.host + loc.pathname + "?upd=1"
    var param = "?next=" + encodeURIComponent(path);

    if (student_id != undefined)
        param += "&uid=" + student_id;

    window.location = url("/v1/accounturl") + param;
}
