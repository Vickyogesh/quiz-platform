// NOTE: 'window.g.image_url' is used by set_exam().
// NOTE: 'window.g.exam_url' is used by load_exam().
(function() {
    function toggle(content) {
        if (content.is(":visible")) {
            content.slideUp("normal");
            content.prev().removeClass('active');
        }
        else {
            content.slideDown("normal");
            content.prev().addClass('active');
        }
    }

    function load_exam(content) {
        var exam_id = content.attr("data-exam-id");
        var url = window.g.exam_url + exam_id;
        $.getJSON(url, function(data){
            set_exam(content, data);
            toggle(content);
        }).error(function(response){
            Aux.showError(response);
        });
    }

    function set_exam(content, data) {
        var questions = data.questions;
        var exam_id = data.exam.id;
        var html = [];
        var fmt_img = '<a href="%2$s.jpg" data-lightbox="image-%1$s"><img src="%2$s.jpg"></a>';
        var fmt_ans = '<span class="question-answer %s">%s</span>';
        var fmt =
            '<div class="tablerow">' +
            '  <div class="content">' +
            '    <div class="cell">%(img)s</div>' +
            '    <div class="cell">' +
            '      <span class="question-id">%(id)s</span> %(text)s</div>' +
            '    <div class="cell">%(ans)s</div></div></div>';

        for (var i in questions) {
            var q = questions[i];
            var opt = {id: q.id, text: q.text, img: "", ans: ""};

            if (q.image != "")
                opt.img = sprintf(fmt_img, exam_id, window.g.image_url + q.image);

            var type = q.is_correct ? "correct" : "wrong";
            var answer = q.answer == 1 ? "V" : "F";
            opt.ans = sprintf(fmt_ans, type, answer);

            html.push(sprintf(fmt, opt));
        }
        html = html.join('');
        content.html(html);
    }

    ExamStat = function () {
        // Convert UTC exam time to local time
        $(".exam-time").each(function () {
            var exam_date = moment($(this).html() + " Z");
            $(this).html(exam_date.toDate().toLocaleString());
        });

        $("#examstat").find(".examrow").click(function(){
            var content = $(this).next();
            var need_load_exam = content.children().length == 0;
            if (need_load_exam)
                load_exam(content);
            else
                toggle(content);
        });
    }

})(this);
