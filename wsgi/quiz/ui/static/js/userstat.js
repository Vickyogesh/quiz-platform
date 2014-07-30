(function() {
    var exam_list;

    function update_topics(range) {
        $(".tablerow .cell .chart").each(function() {
            $(this).html("");
            var value;
            if (range == "data-e-all") {
                value = 0;
                var lst = [parseInt($(this).attr("data-e-current")),
                    parseInt($(this).attr("data-e-week")),
                    parseInt($(this).attr("data-e-week3"))];
                var count = 0;
                for (var i in lst) {
                    if (lst[i] >= 0) {
                        ++count;
                        value += lst[i];
                    }
                }

                if (!count)
                    value = -1;
                else
                    value /= count;
            }
            else
                value = parseInt($(this).attr(range));
            draw_pie(this, value);
        });
    }

    function draw_exams(id, range, w, h) {
        var key = range.substring(7);
        var i;
        var data;
        var examX = [];
        var examY = [];
        var count = 0;

        if (key == "all") {
            data = [].concat(exam_list['week3'], exam_list['week'],
                exam_list['current']);
        }
        else
            data = exam_list[key];

        for (i = 0; i < data.length; i++) {
            if (data[i].status != "passed" && data[i].status != "failed")
                continue;
            examX.push(count);
            examY.push(40 - data[i].errors);
            count++;
        }

        for (; count < 3; count++) {
            examX.push(count);
        }

        var p = Raphael(id, w, h);
        p.setViewBox(0, 0, w, h, true);

        p = p.linechart(10, 0, w - 12, h - 10,
            [examX, [0, count]],
            [examY, [36, 36], [0, 40]], {
                symbol: ["circle"],
                axis: "0 0 1 1",
                axisxstep: examX.length || 2,
                colors: ['#2479cc', '#CCC', 'transparent'],
                dash: ["", "-"]
            });

        var l;
        for (i = 0, l = p.axis.length; i < l; i++ ) {
            // change the axis and tick-marks
            p.axis[i].attr("stroke", "#0459ac");

            // change the axis labels
            var axisItems = p.axis[i].text.items;
            for( var ii = 0, ll = axisItems.length; ii < ll; ii++ ) {
                axisItems[ii].attr("fill", "#0459ac");
            }
        }

        // Set exam circle size.
        p.symbols[0].attr("r", 4);

        // Update x-axis texts
        var xText = p.axis[0].text.items;
        for(i in xText){
            var nVal = parseInt(xText[i].attr('text')) + 1;
            xText[i].attr({'text': nVal + ''});
        }
        var lab = p.label($('#' + id).width() / 2, 8, "Statistiche esami");
        lab.attr([{fill:"none"}, {fill:"#0459ac", "font-weight": "bold"}]);

        var id = "#" + id + " svg";
        $(id).attr("width", "100%");
        $(id).attr("height", "100%");
    }

    function update_stat(range) {
        $("#exam_chart").html("");
        update_topics(range);
        draw_exams("exam_chart", range, 300, 150);
    }

    var current_range = "data-e-all";
    function on_history_range() {
        var a = $(this).find("a");
        a.blur();
        var new_range = a.attr("data-e-range");
        if (current_range == new_range)
            return;
        current_range = new_range;
        $(".navbar-nav li").removeClass("active");
        $(this).addClass("active");
        update_stat(current_range);
    }

    UserStat = function(exam_data) {
        exam_list = exam_data;
        update_stat(current_range);
        $(".navbar-nav li").click(on_history_range);

        $("#exams").find("a").click(function() {
            var range = current_range.substring(7);
            window.location = window.g.exam_url + range;
        });
    }
})();
