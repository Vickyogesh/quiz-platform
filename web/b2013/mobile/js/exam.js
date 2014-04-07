$("#page-exam").bind("pageinit", function() {
    var exam_timer;
    var time_limit;
    var exam_time_el = $("#page-exam .ui-header h3 > span#time");

    var mgr = createExamQuestionManager({
        pageId: "#page-exam",
        headerId: "#page-exam .ui-header h3 > span#count"
    });

    mgr.getQuestionsUrl = function() { return "/v1/exam"; };
    mgr.sendAnswersUrl = function() {
        return "/v1/exam/" + sessionStorage.getItem("examid");
    };

    // Exam time counting.

    function timeCounter() {
        --time_limit;

        var nMin = Math.floor(time_limit / 60);
        var nSec = time_limit % 60;
        var strMin = '' + nMin;
        var strSec = '' + nSec;
        if (strMin < 10) strMin = '0' + nMin;
        if (strSec < 10) strSec = '0' + nSec;
        
        exam_time_el.html(strMin + ":" + strSec);

        // If time is passed then send exam answers
        if (time_limit == 0) {
            clearInterval(exam_timer);
            mgr.sendAnswers(self.showNumErrors);
            return;
        }
        // Extra check to be sure we dont go below zero.
        else if (time_limit < 0) {
            clearInterval(exam_timer);
            exam_time_el.html("00:00");
            console.log("exam timer is still counting!");
            return;
        }
    }

    var old_setQuestions = mgr.setQuestions;
    mgr.setQuestions = function(questions) {
        time_limit = 1800; // 30 min for exam.
        exam_timer = window.setInterval(timeCounter, 1000);
        timeCounter();
        old_setQuestions.call(this, questions);
    }

    // Stop timer on exit.
    mgr.onLeave = function() { clearInterval(exam_timer); }

    // Send exam actions.

    // After exam sending we show number of errors and
    // then navigate to exam review page.
    function afterSendExam() {
        var msg = 'Hai commesso ' + this.total_errors + ' errori.<br/>';

        $('<div>').simpledialog2({
            mode: 'button',
            headerText: "Esame",
            headerClose: false,
            buttonPrompt: msg,
            buttons: {
                'Ok': {'click': function() {
                    $.mobile.changePage("#page-exam-review");
                }}
            }
        });
    }

    // Send exam answers. Additional action is auto set answers
    // if not all questions answered.
    var func = mgr.sendAnswers;
    mgr.sendAnswers = function(onOk, onError) {
        // If back or logout action is requested then
        // just do it without answers sending.
        if (onOk == this.back || onOk == this.logout) {
            onOk.call(this);
            return;
        }

        $.mobile.showPageLoadingMsg("b", "Attendere prego.");
        clearInterval(exam_timer);
        func.call(this, afterSendExam);
    };

    mgr.init();
});
