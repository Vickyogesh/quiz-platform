function editAccount() {
    $.getJSON(url("/v1/accounturl"), function(data) {
        if (data.status != 200) {
            aux_showJSONError(data);
            return;
        }

        var url = data.url;
        if (url == "")
            return;

        var loc = window.location
        var path = loc.protocol + "//" + loc.host + loc.pathname + "?upd=1"
        url += '&next=' + encodeURIComponent(path)
        window.location=url;
    });
}
