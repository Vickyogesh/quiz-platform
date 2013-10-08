function editAccount() {
    var loc = window.location
    var path = loc.protocol + "//" + loc.host + loc.pathname + "?upd=1"
    var param = '?next=' + encodeURIComponent(path);
    window.location = url("/v1/accounturl") + param;
}
