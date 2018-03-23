(function() {
    Question = Backbone.Model.extend({
        isAnswered: function() {
            return this.has("user_answer");
        },
        isCorrectAnswer: function() {
            return this.get("answer") == this.get("user_answer");
        },
        isTrueAnswer: function() {
            return this.get("user_answer") == 1;
        },
        setAnswer: function(val) {
            this.set("user_answer", val ? 1 : 0);
        },
        isSaved: function() {
            return this.has("saved");
        },
        markSaved: function() {
            this.set("saved", 1);
        }
    });

    QuestionList = Backbone.Collection.extend({
       model: Question
    });

    QuizModel = Backbone.Model.extend({
        defaults: {
            topic_id: 0,
            title: "",

            index: -1,
            last_answered_index: -1,
            total_errors: 0,
            show_answers: false,
            can_answer: true
        },

        initialize: function() {
            this.is_can_load_more = true;
            this.img_preloader = new Image;
            this.questions = new QuestionList;
        },

        reset: function() {
            this.questions.reset();
            this.is_can_load_more = true;
            this.set("total_errors", 0);
            this.set("last_answered_index", -1);
            this.set("index", -1);
        },

        get_url: function(name) {
            return this.get("urls")[name];
        },

        getImageUrl: function(name) {
            if (name == "" || name === undefined || name === null )
                return null;
            return this.get_url("image") + name + ".jpg";
        },

        getQuizUrl: function() {
            return this.get_url("quiz") + this.get("topic_id");
        },

        preloadNextImage: function() {
            var q = this.questions.at(this.get("image") + 1);
            if (q !== undefined)
                this.img_preloader.src = this.getImageUrl(q.image);
        },

        getTopQuestions: function() {
            var index = this.get("index");
            return [this.questions.at(index - 2), this.questions.at(index - 1)];
        },
        getBottomQuestions: function() {
            var index = this.get("index");
            return [this.questions.at(index + 1), this.questions.at(index + 2)];
        },
        getCurrentQuestion: function() {
            return this.questions.at(this.get("index"));
        },
        getCurrentQuestionImage: function() {
            return this.getImageUrl(this.getCurrentQuestion().get("image"));
        },

        setAnswer: function(val) {
            if (this.get("can_answer") == true) {
                var question = this.getCurrentQuestion();
                if (question.isAnswered())
                    return;
                question.setAnswer(val);
                if (!question.isCorrectAnswer())
                    this.set("total_errors", this.get("total_errors") + 1);
                this.set("last_answered_index", this.get("index"));
                console.log(this.get("ai"));

                if (this.get("ai")) {
                    this.postAiAnswer(question.get("id"), question.isCorrectAnswer())
                }else {
                    this.moveToNext();
                }
            }
        },

        moveToNext: function() {
            var index = this.get("index");
            if (this.get("ai")){
                this.set("index", index + 1);
                return
            }
            if (index + 3 >= this.questions.length
                && this.is_can_load_more) {
                this.loadMoreQuestions();
            }
            else if (index + 1 < this.questions.length) {
                this.set("index", index + 1);
                this.preloadNextImage();
            }
            else if (index + 1 == this.questions.length) {
                var self = this;
                this.sendCurrentAnswers(function() {
                    self.trigger("done");
                });
            }
        },

        getDataToSend: function(data, questions_to_mark) {
            var ids = [];
            var answers = [];

            this.questions.each(function(question, index) {
                if (question.isAnswered() && !question.isSaved()) {
                    ids.push(question.get("id"));
                    answers.push(question.get("user_answer"));
                    questions_to_mark.push(index);
                }
            });

            data.questions = ids;
            data.answers = answers;
        },

        sendCurrentAnswers: function(ok_callback) {
            var data = {};
            var questions_to_mark = [];
            this.getDataToSend(data, questions_to_mark);

            // Nothing to send...
            if (data.questions.length == 0) {
                ok_callback();
                return;
            }

            var self = this;
            var url = this.getQuizUrl();

            Aux.postJson(url, data, function(response) {
                _.each(questions_to_mark, function(index) {
                    self.questions.at(index).markSaved();
                });
                ok_callback(response);
            }).error(function(response) {
                self.trigger("error:save", response, ok_callback);
            });
        },

        loadMoreQuestions: function(force) {
            var url = this.getQuizUrl();
            var exclude = [];

            this.questions.each(function (question) {
                if (question.isAnswered())
                    exclude.push(question.get("id"));
            });

            var params = {};

            if (exclude.length != 0)
                params.exclude = exclude.toString();

            var t_lst = Aux.getUrlParameterByName('t_lst');

            if (t_lst){
                params.t_lst = t_lst;
            }

            if (force == true) {
                params.force = true;
                // We don't need to excude questions since we restart quiz.
                delete params.exclude;
            }

            params = decodeURIComponent($.param(params));
            if (params.length != 0)
                url += "?" + params;

            var self = this;
            this.sendCurrentAnswers(function() {
                $.getJSON(url, function(data) {
                    if (force)
                        self.reset();
                    self.addQuestions(data.questions);

                    if (force)
                        self.set("index", 0);
                    else
                        self.moveToNext();
                }).error(function(response) {
                    self.trigger("error:load", response);
                });
            });
        },

        loadAiQuestion: function () {
            var self = this;

            var url = this.get_url("ai_question");

            var exclude = [];

            this.questions.each(function(question, index) {
                exclude.push(question.get("id"))
            });

            var data = {"quiz_type": this.get("data")["quiz_type"],
                "quiz_session": this.get("data")["session_id"],
                "num_ex": this.get("data")["num_ex"],
                "chapter_id": this.get("data")["chapter"],
                "topic_id": this.get("data")["topic"],
                "exclude": exclude
            };


            Aux.postJson(url, data, function (res) {
                if (res['status'] === 416) {
                    self.trigger("done")
                    return
                }
                if (res['status'] !== 200){
                    alert(res['description']);
                    return
                }
                self.addQuestions([res]);
                self.moveToNext();
            })

        },

        postAiAnswer : function (quest_id, answer) {
            var self = this;

            var url = this.get_url("ai_answer");

            var data = {"quiz_session": this.get("data")["session_id"],
                "num_quest": this.get("data")["num_ex"],
                "correct": answer,
                "quest_id": quest_id
            };

            Aux.postJson(url, data, function (res) {
                console.log(res);
                if (res['status'] !== 200){
                    alert(res['description']);
                    return
                }
                self.showMetric(res['data']);
                self.loadAiQuestion()
            })

        },

        showMetric: function (data) {
            $("#ai_progress").html((data['progress'] * 100).toFixed(2));
            $("#ai_score").html((data['score'] * 100).toFixed(2));
        },

        addQuestions: function(questions) {
            if (questions.length < 40)
                this.is_can_load_more = false;
            this.questions.add(questions);
        },

        showNext: function() {
            var index = this.get("index") + 1;
            var last_answered_index = this.get("last_answered_index");

            if (index <= last_answered_index + 1 && index < this.questions.length)
                this.set("index", index);
        },
        showPrevious: function() {
            var index = this.get("index");
            if (index > 0)
                this.set("index", index - 1);
        }
    });
})();
