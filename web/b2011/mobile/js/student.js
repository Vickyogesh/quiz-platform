$("#page-student").bind("pageinit", function() {
    $("#bttLogout").click(function() {
        window.qsid = null;
        window.name = null;
        aux_deleteCookie("QUIZSID", '/');
        $.mobile.changePage("index.html", {reloadPage: true});
    });
    $("#page-student").bind('pageshow', function() {
        $("#page-student h1").html(window.name);
        updateContentSize();
    });
    $("#page-student").bind('orientationchange', function() {
        updateContentSize();
    });

    var resizeTimer;
    $(window).resize(function() {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(updateContentSize, 100);
    });    
});
