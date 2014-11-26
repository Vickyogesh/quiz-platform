$("#page-quiz").bind("pageinit", function() {
    var mgr = createQuestionManager({
        pageId: "#page-quiz",
        headerId: "#page-quiz .ui-header h3 > span"
    });

    mgr.getQuestionsUrl = function(force) {
        var topic = sessionStorage.getItem("topic");
        var url = url("/v1/quiz/" + topic);

        if (force == true)
            url += "?force=true";
        return url;
    };
    
    mgr.sendAnswersUrl = function() {
        return url("/v1/quiz/" + sessionStorage.getItem("topic"));
    }

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

        msg += "Hai risposto a tutte le domande di questo argomento! Continuare comunque?";

        $('<div>').simpledialog2({
            mode: 'button',
            headerText: "Quiz",
            headerClose: false,
            buttonPrompt: msg,
            buttons: {
                'Ok': {'click': function() {
                    mgr.getQuestions(mgr.setQuestions, true);
                }},
                'Cancel': {
                    click: function() { mgr.back(); },
                    icon: "delete", theme: "c"
                }
            }
        });
    }

    mgr.init();
});
