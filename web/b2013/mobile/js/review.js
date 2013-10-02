$("#page-review").bind("pageinit", function() {
    var mgr = createQuestionManager({
        pageId: "#page-review",
        headerId: "#page-review .ui-header h3"
    });

    mgr.getQuestionsUrl = function() { return "/v1/errorreview"; };
    mgr.sendAnswersUrl = mgr.getQuestionsUrl;

    var func = mgr.setQuestions;
    mgr.setQuestions = function (questions) {
        if (questions.length != 0) {
            func.call(this, questions);
            return;
        }

        var msg = "";
        if (this.total_errors != 0) {
            msg += 'Hai commesso ' + this.total_errors + ' errori.<br/>';
            this.total_errors = 0;
        }

        msg += "There are no wrong answers!";

        $('<div>').simpledialog2({
            mode: 'button',
            headerText: "Ripasso errori",
            headerClose: false,
            buttonPrompt: msg,
            buttons: {
                'Ok': {'click': function() { mgr.back(); }}
            }
        });
    }

    mgr.init();
});
