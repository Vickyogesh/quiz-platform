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
        var fmt_img = '<a href="%2$s.jpg" rel="image-%1$s" class="cbox"><img src="%2$s.jpg"></a>';
        var fmt_ans = '<span class="question-answer %s">%s</span>';
        var expl_butt = '<a href="javascript:void(0);"><span class="exam_expl_butt '+exam_id+'_lamp"' +
            ' data-exam_id="'+exam_id+'"></span></a>';
        var expl_wrap = '<div class="exam_expl_wrap '+exam_id+'_exam">%s</div>';
        var fmt =
            '<div class="tablerow">' +
            '  <div class="content">' +
            '    <div class="cell">%(img)s</div>' +
            '    <div class="cell">' +
            '      <span class="question-id">%(id)s</span> %(text)s</div>' +
            '    <div class="cell">%(expl_butt)s %(ans)s</div></div></div>%(expl_wrap)s';

        for (var i in questions) {
            var q = questions[i];
            var opt = {id: q.id, text: q.text, img: "", ans: "", expl_butt: "", expl_wrap: ""};

            if (q.image != "")
                opt.img = sprintf(fmt_img, exam_id, window.g.image_url + q.image);
            var type;
            if (q.is_correct){
                type = "correct";
            }else {
                type = "wrong";
                if (q.explanation){
                    opt.expl_butt = expl_butt;
                    opt.expl_wrap = sprintf(expl_wrap, q.explanation);
                }
            }
            var answer = q.answer == 1 ? "V" : "F";
            opt.ans = sprintf(fmt_ans, type, answer);

            html.push(sprintf(fmt, opt));
        }
        html = html.join('');
        content.html(html);
        content.find("a.cbox").colorbox();
        showExplanations();
    }

    function showExplanations() {
        var lamp = $(".exam_expl_butt");

        lamp.off('click').on('click', function () {
            var el = $(this);
            var exam_id = el.attr('data-exam_id');
            var exam_lamp = $("."+exam_id+"_lamp");
            exam_lamp.toggleClass('active');
            if (exam_lamp.hasClass('active')){
                $('.'+exam_id+'_exam').slideDown('fast')
            }else {
                $('.'+exam_id+'_exam').slideUp('fast')
            }
        });

    }

    ExamStat = function () {
        // Convert UTC exam time to local time
        $(".exam-time").each(function () {
            $(this).html(Aux.strFromISOUTC($(this).html()));
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

}).call(this);
