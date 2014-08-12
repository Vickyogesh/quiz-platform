(function() {
    QuestionView = Backbone.View.extend({
        events: {
            "click .true": "onBttTrue",
            "click .false": "onBttFalse"
        },

        constructor: function() {
            this.quiz_model = arguments[0].quiz_model;
            Backbone.View.prototype.constructor.apply(this, arguments);
        },

        initialize: function() {
            this.show_answers = false;
            this.text_el = this.$("#text");
            this.cells = this.$(".qcell");
            this.ansbox_el = this.$(".ansbox");
            this.btt_true = this.$(".true");
            this.btt_false = this.$(".false");
            this.listenTo(this.quiz_model, "change:show_answers", this.renderAnswerBox);
        },

        render: function() {
            this.btt_true.removeClass("sel");
            this.btt_false.removeClass("sel");

            if (this.model === undefined) {
                this.cells.addClass("hidden");
            }
            else {
                this.cells.removeClass("hidden");
                this.text_el.html(this.model.get("id") + " | " + this.model.get("text"));

                if (this.model.isAnswered()) {
                    if (this.model.isTrueAnswer()) {
                        this.btt_true.addClass("sel");
                    }
                    else {
                        this.btt_false.addClass("sel");
                    }
                }
                this.renderAnswerBox();
            }
            return this;
        },

        renderAnswerBox: function() {
            this.ansbox_el.removeClass("correct");
            this.ansbox_el.removeClass("incorrect");
            if (this.model !== undefined) {
                if (this.model.isAnswered()) {
                    if (this.quiz_model.get("show_answers")) {
                        this.ansbox_el.addClass(this.model.isCorrectAnswer()
                            ? "correct" : "incorrect");
                    }
                }
            }
        },

        setModel: function(model) {
            if (this.model !== undefined)
                this.stopListening(this.model);

            this.model = model;
            if (model !== undefined)
                this.listenTo(model, "change", this.render);
            this.render();
        },

        // Event handlers

        onBttTrue: function() {
            this.trigger("answer", true);
        },
        onBttFalse: function() {
            this.trigger("answer", false);
        }
    });


    AnswersSwitchView = Backbone.View.extend({
        events: {
            "change": "onChange"
        },

        initialize: function() {
            this.opt_yes_el = this.$("#opt_yes");
        },

        onChange: function() {
            this.trigger("change", this.opt_yes_el.prop("checked"));
        },

        setEnabled: function(state) {
            if (state)
                this.$("label").removeAttr("disabled");
            else
                this.$("label").attr("disabled", "true");
        }
    });

    QuizView = Backbone.View.extend({
        events: {
            "click #btt-done": "onBttFinish",
            "mousewheel": "onWheel"
        },

        createModel: function(params) {
            return new QuizModel({
                urls: params.urls,
                topic_id: params.data.topic
            });
        },

        constructor: function() {
            var params = arguments[0];
            this.model = this.createModel(params);
            this.model.questions.reset(params.data.questions);
            this.msgbox = new MessageBox({el: params.msgbox_el});
            this.labels = params.labels;
            this.urls = params.urls;
            Backbone.View.prototype.constructor.apply(this, arguments);
        },

        initialize: function() {
            this.question_image_a_el = this.$("#question_image");
            this.question_image_el = this.question_image_a_el.find("img");

            this.switch_view = new AnswersSwitchView({
                el: this.$("form.navbar-form")
            });

            this.top_rows = [
                new QuestionView({quiz_model: this.model, el: this.$("#row0")[0]}),
                new QuestionView({quiz_model: this.model, el: this.$("#row1")[0]})
            ];

            this.active_row = new QuestionView({
                quiz_model: this.model,
                el: this.$("#row2")
            });

            this.bottom_rows = [
                new QuestionView({quiz_model: this.model, el: this.$("#row3")}),
                new QuestionView({quiz_model: this.model, el: this.$("#row4")})
            ];

            this.listenTo(this.switch_view, "change", this.onSwitch);
            this.listenTo(this.active_row, "answer", this.onAnswer);
            this.listenTo(this.model, "change:index", this.onModelChange);
            this.listenTo(this.model, "error:save", this.onModelSaveError);
            this.listenTo(this.model, "error:load", this.onModelLoadError);
            this.listenTo(this.model, "done", this.onDone);

            this.msgbox.on("show", function() {
                this.switch_view.setEnabled(false);
                this.$("#btt-done").attr("disabled", "true");;
            }.bind(this));
            this.msgbox.on("hide", function() {
                this.switch_view.setEnabled(true);
                this.$("#btt-done").removeAttr("disabled");
            }.bind(this));

            if (this.model.questions.length == 0)
                this.showDone();
            else
                this.model.set("index", 0);

            this.$("a.cbox").colorbox();
        },

        _setQuestions: function(questions, rows) {
            _.each(_.zip(questions, rows), function(item) {
                item[1].setModel(item[0]);
            });
        },

        _setImage: function(url) {
            if (url === undefined || url === null)
                this.question_image_a_el.hide();
            else {
                this.question_image_a_el.attr("href", url);
                this.question_image_a_el.css("background-image", "url(" + url + ")");
                this.question_image_a_el.show();
            }
        },

        showLoadError: function(msg, tryagain_callback) {
            function back() {
                window.location = this.urls.back;
            }
            function close() {
                this.msgbox.hide();
            }
            this.msgbox.show({
                "text": msg,
                "icon": "glyphicon-remove-circle",
                "buttons": [
                    {
                        text: this.labels.btt_back, type: "btn-success",
                        icon: "glyphicon-arrow-left",
                        callback: back.bind(this)
                    },
                    {
                        text: this.labels.btt_close, type: "btn-danger",
                        callback: close.bind(this)
                    },
                    {
                        text: this.labels.btt_try_again, type: "btn-primary",
                        icon: "glyphicon-repeat",
                        callback: tryagain_callback
                    }
                ]
            });
        },

        showDone: function(show_errors) {
            function back() {
                window.location = this.urls.back;
            }
            function restart() {
                this.model.loadMoreQuestions(true);
                this.msgbox.hide();
            }
            function review() {
                this.msgbox.hide();
            }

            var buttons = [
                {
                    text: this.labels.btt_back, type: "btn-success",
                    icon: "glyphicon-arrow-left",
                    callback: back.bind(this)
                },
                {
                    text: this.labels.btt_restart, type: "btn-primary",
                    icon: "glyphicon-repeat",
                    callback: restart.bind(this)
                }
            ];

            var text = this.labels.done;
            if (show_errors == true) {
                text += "<br/>" + sprintf(this.labels.done_info,
                    {errors: this.model.get("total_errors")});

                buttons.push({
                    text: this.labels.btt_review, type: "btn-default",
                    icon: "glyphicon-eye-open",
                    callback: review.bind(this)
                });
            }

            this.msgbox.show({
                "text": text,
                "icon": "glyphicon-ok-circle",
                "buttons": buttons
            });
        },

        showFinish: function() {
            function back() {
                window.location = this.urls.back;
            }
            function review() {
                this.msgbox.hide();
            }

            var buttons = [
                {
                    text: this.labels.btt_back, type: "btn-success",
                    icon: "glyphicon-arrow-left",
                    callback: back.bind(this)
                },
                {
                    text: this.labels.btt_review, type: "btn-default",
                    icon: "glyphicon-eye-open",
                    callback: review.bind(this)
                }
            ];

            var text = sprintf(this.labels.done_info,
                    {errors: this.model.get("total_errors")});

            this.msgbox.show({
                "text": text,
                "buttons": buttons
            });
        },

        onWheel: function(event) {
            if (event.deltaY > 0)
                this.model.showPrevious();
            else if (event.deltaY < 0)
                this.model.showNext();
        },

        onBttFinish: function() {
            this.model.sendCurrentAnswers(this.showFinish.bind(this));
        },

        onSwitch: function(show_answers) {
            this.model.set("show_answers", show_answers);
        },

        onAnswer: function(val) {
            if (this.model.get("index") != -1)
                this.model.setAnswer(val);
        },

        onModelChange: function() {
            this._setQuestions(this.model.getTopQuestions(), this.top_rows);
            this._setQuestions(this.model.getBottomQuestions(), this.bottom_rows);
            var question = this.model.getCurrentQuestion();
            this.active_row.setModel(question);
            this._setImage(this.model.getCurrentQuestionImage());
        },

        onModelSaveError: function(response, ok_callback) {
            this.showLoadError(this.labels.error_get, function() {
                this.model.sendCurrentAnswers(ok_callback);
            }.bind(this));
        },

        onModelLoadError: function(response) {
            this.showLoadError(this.labels.error_get, function() {
                this.model.loadMoreQuestions();
            }.bind(this));
        },
        
        onDone: function () {
            this.showDone(true);
        }
    });
})();
