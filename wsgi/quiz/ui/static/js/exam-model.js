(function() {
    ExamModel = QuizModel.extend({
        defaults: _.extend({}, QuizModel.prototype.defaults,{
            max_errors: 4
        }),

        initialize: function() {
            QuizModel.prototype.initialize.apply(this, arguments);
            this.is_can_load_more = false;
        },

        getQuizUrl: function() {
            return this.get_url("exam") + this.get("exam_id");
        },

        moveToNext: function() {
            var index = this.get("index");
            if (index + 1 < this.questions.length) {
                this.set("index", index + 1);
                this.preloadNextImage();
            }
            else if (index + 1 == this.questions.length)
                self.trigger("done");
        },

        // Allows to show all questions, event unanswered.
        showNext: function() {
            var index = this.get("index") + 1;
            if (index < this.questions.length)
                this.set("index", index);
        },
        // Set answer even for already answered question.
        setAnswer: function(val) {
            if (this.get("can_answer") == true) {
                var question = this.getCurrentQuestion();
                question.setAnswer(val);
                this.trigger("answer", this.get("index"));
                if (!question.isCorrectAnswer())
                    this.set("total_errors", this.get("total_errors") + 1);
            }
        },

        getDataToSend: function(data, questions_to_mark) {
            var ids = [];
            var answers = [];

            this.questions.each(function(question, index) {
                var ans;
                if (question.isAnswered())
                    ans = question.get("user_answer");
                else
                    ans = question.get("answer") == 1 ? 0 : 1;

                ids.push(question.get("id"));
                answers.push(ans);
                questions_to_mark.push(index);
            });

            data.questions = ids;
            data.answers = answers;
        }
    });
})();
