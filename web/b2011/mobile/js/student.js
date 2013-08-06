$("#page-student").bind("pageinit", function() {
  function layout_grid(id) {
      aux_layoutGrid(id);
      var p = $(id).parent();
      var pw = p.width();
      var ph = p.height();
      var grid = $(id);

      ph -= 30; // Content margin.
      ph -= 10; // Button margin.

      if (pw > ph)
          ph /= 2;
      else
          ph /= 3;
      $(id + " .rect-button").css("height", ph + "px");
      $(id + " .rect-button").css("line-height", ph + "px");
  }

  $("#page-student #bttLogout").click(function() {
      window.qsid = null;
      window.name = null;
      aux_busy(true);
      $.ajax("/v1/authorize/logout").always(function() {
          aux_busy(false);
          $.mobile.changePage("#page-login");
      });
  });

  $("#page-student").bind('pageshow', function() {
      $("#page-student h1").html(window.name);
      $("#page-student").page();
      layout_grid("#menugrid");
  });
  $("#page-student").bind('orientationchange', function() {
      layout_grid("#menugrid");
  });

  layout_grid("#menugrid");

  var resizeTimer;
  $(window).resize(function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function(){ layout_grid("#menugrid"); }, 100);
  });
});
