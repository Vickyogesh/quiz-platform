$("#page-quiz-chapters").bind("pageinit", function() {
  function fill_chapter() {
      var html = "";
      for (var i = 0; i < 5; i++) {
          html += '<div class="tp ui-block-a">' + (5 * i + 1) + '</div>'
               + '<div class="tp ui-block-b">' + (5 * i + 2) + '</div>'
               + '<div class="tp ui-block-c">' + (5 * i + 3) + '</div>'
               + '<div class="tp ui-block-d">' + (5 * i + 4) + '</div>'
               + '<div class="tp ui-block-e">' + (5 * i + 5) + '</div>';
      }
      $("#page-quiz-chapters #chapters").html(html);
  }

  function layout() {
    var p = $("#page-quiz-chapters");
    var ph = p.height();
    var grid = $("#chapters");
    var gh = grid.height();
    var top = grid.position().top;
    var h = ph - top - 60;
    var itemh = h / 5;
    $("#chapters > div").css("height", itemh + "px");
    $("#chapters > div").css("line-height", itemh + "px");
  }

  $("#page-quiz-chapters").bind('pageshow', function() {
      layout();
  });
  $("#page-quiz-chapters").bind('orientationchange', function() {
      layout();
  });

  var resizeTimer;
  $(window).resize(function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function(){ layout(); }, 100);
  });

  fill_chapter();
  layout();
  $("#page-quiz-chapters #chapters > div").click(function() {
    var chapter = $(this).html();
    sessionStorage.setItem("ch", chapter);
    //$("#page-quiz-chapters #chapters").attr('active-chapter', chapter);
    $.mobile.changePage("#page-quiz-topics", {transition: "slide"});
  });

  $("#page-quiz-chapters #bttLogout").click(function() {
    window.name = null;
    aux_busy(true);
    $.ajax("/v1/authorize/logout").always(function() {
        aux_deleteServicesCookies();
        aux_busy(false);
        $.mobile.changePage("#page-login");
    });
  });
  $("#page-quiz-chapters #bttBack").click(function() {
    $.mobile.changePage("#page-student",
                        {transition: "slide", reverse: true});
  });

});
