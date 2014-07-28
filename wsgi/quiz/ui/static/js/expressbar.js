function init_express_bar(bar_id, parent_id, control_el_id) {
  var bar_el = $(bar_id);
  var bar_hidden = true;
  var parent_el = $(parent_id);
  var parent_el_width = 0;
  var control_el = $(control_el_id);

  function do_resize() {
    if (!bar_hidden) {
      var w = parent_el.outerWidth();
      if (w != parent_el_width) {
        $('#fixedbar').width(w);
        parent_el_width = w;
      }
    }
  }

  function handle_show() {
    var top = control_el.offset().top - $(window).scrollTop();

    if (top < 0 && bar_hidden) {
      bar_hidden = false;
      do_resize();
      bar_el.show();
    } else if (top >= 0 && !bar_hidden) {
      bar_el.hide();
      bar_hidden = true;
    }
  }

  bar_el.hide();
  handle_show();

  $(window).resize(do_resize);
  $(document).scroll(handle_show);
}
