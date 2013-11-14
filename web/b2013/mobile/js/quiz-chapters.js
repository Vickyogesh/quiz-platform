$("#page-quiz-chapters").bind("pageinit", function() {
  function fill_chapter() {
    var chapter_area = [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3,
                        3, 3, 3, 3, 3, 4, 4, 5, 6, 6, 6, 7, 7];
    var html = "";

    function chapter_div(ui_block, chapter_id) {
      var fmt = '<div class="{0} tp area{1}">{2}</div>';
      return fmt.format(ui_block, chapter_area[chapter_id - 1], chapter_id);
    }

    for (var i = 0; i < 5; i++) {
      html += chapter_div("ui-block-a", 5 * i + 1)
           + chapter_div("ui-block-b", 5 * i + 2)
           + chapter_div("ui-block-c", 5 * i + 3)
           + chapter_div("ui-block-d", 5 * i + 4)
           + chapter_div("ui-block-e", 5 * i + 5);
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
