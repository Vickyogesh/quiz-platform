function draw_pie(id, error_percent, opts) {
  var stroke = "#FFF";
  var values;
  var colors;

  if (opts === undefined)
    opts = {}

  if (error_percent == 0 || error_percent == 100) {
    values = [100];
    colors = ['#FFF'];
  }
  else if (error_percent > 0 ) {
    values = [100 - error_percent, error_percent];
    colors = ['#2479cc', '#FFF'];
  }
  else {
    error_percent = -1;
    if (opts.showEmpty) {
      values = [100];
      colors= ["#FFF"];
      stroke = "#CCC";
    }
    else
      return;
  }

  var p = Raphael(id);

  var w = opts.width || 10;
  var h = opts.height || 10;
  var r = opts.radius || 8;
  var a = opts.angle || -90;

  if (opts.resizable) {
    p.setViewBox(0, 0, w, h, true);
    w /= 2;
    h /= 2;
    p.setSize("100%", "auto");
  }

  p = p.piechart(w, h, r, values, {
      stroke: stroke,
      strokewidth: 2,
      colors: colors,
      angle: a
  });

  if (error_percent == 0)
    p.series.items[0].attr({opacity : 100, fill: "#2479CC"});
  else if (error_percent == 100)
    p.series.items[0].attr({opacity : 100, fill: "#CCC"});
  else if (error_percent > 0)
    p.series.items[1].attr({opacity : 100, fill: "#CCC"});
}
