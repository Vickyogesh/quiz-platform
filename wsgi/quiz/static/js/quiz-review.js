(function () {
    QuizReviewModel = QuizModel.extend({
        getQuizUrl: function() {
            return this.get_url("quiz");
        }
    });

    QuizReviewView = QuizView.extend({
        createModel: function(params) {
            return new QuizReviewModel({urls: params.urls});
        },

        showDone: function(show_errors) {
            if (show_errors) {
                this.showFinish();
                return;
            }

            function back() {
                window.history.back();
            }
            this.msgbox.show({
                "text": this.labels.done,
                "icon": "glyphicon-ok-circle",
                "buttons": [{
                    text: this.labels.btt_back, type: "btn-success",
                    icon: "glyphicon-arrow-left",
                    callback: back.bind(this)
                }]
            });
        }
    });
})();
