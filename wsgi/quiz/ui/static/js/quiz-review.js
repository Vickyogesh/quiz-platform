(function () {
    QuizReviewModel = QuizModel.extend({
        getQuizUrl: function() {
            return this.get("quiz_url");
        }
    });

    QuizReviewView = QuizView.extend({
        createModel: function(params) {
            return new QuizReviewModel({
                image_url: params.image_url,
                quiz_url: params.quiz_url
            });
        },

        showDone: function(show_errors) {
            if (show_errors) {
                this.showFinish();
                return;
            }

            function back() {
                window.location = this.back_url;
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
