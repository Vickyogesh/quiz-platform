$("#page-exam-review").bind("pageinit", function() {
    function processError(data) {
        var user = sessionStorage.getItem('quizutype');
        if (data.status == 403 && user == "guest") {
            $('<div>').simpledialog2({
                mode: 'button',
                headerText: "Errori",
                headerClose: false,
                buttonPrompt: "Numero di sessioni per utenti esterni esaurite. Si prega di ritornare tra un'ora.",
                buttons: {
                    'Ok': {'click': function() { aux_logout(); }}
                }
            });
        }
        else
            aux_showError(data.description);
    }

    function showExamReview(data) {
        var answers_el = $("#page-exam-review #answers");

        var html = "";
        var img = '<img src="/img/{0}.jpg">';
        var row =
            '<div class="row">' +
            '<div class="cell">{0}</div>' +
            '<div class="cell">{1}</div>' +
            '<div class="cell"><div class="result {2}">{3}</div></div>' +
            '</div>';

        var ans_type, ans, image;
        var q;
        for (i = 0; i < data.questions.length; i++) {
            q = data.questions[i];
            ans_type = q.is_correct == 1 ? "good" : "bad";
            ans = q.answer == 1 ? "V" : "F";

            if (q.image != "")
                image = img.format(q.image);
            else
                image = "";

            html += row.format(image, q.text, ans_type, ans);
        }

        answers_el.html(html);
    }

    $("#page-exam-review #bttLogout").click(aux_logout);
    $("#page-exam-review #bttBack").click(function() {
        $.mobile.changePage("#page-student",
                            {transition: "slide", reverse: true});
    });

    $("#page-exam-review").bind('pageshow', function() {
        var exam_id = sessionStorage.getItem("examid");
        var exam_el = $("#page-exam-review .ui-header h3 > span");
        exam_el.html(exam_id);

        aux_busy(true);
        $.getJSON("/v1/exam/" + exam_id, function(data) {
            aux_busy(false);
            if (data.status != 200)
                processError(data);
            else
                showExamReview(data);
        });
    });
});
