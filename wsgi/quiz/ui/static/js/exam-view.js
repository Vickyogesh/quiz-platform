(function() {
    ExamTimerView = Backbone.View.extend({
        constructor: function() {
            var params = arguments[0];
            this.current = params.total;
            Backbone.View.prototype.constructor.apply(this, arguments);
        },

        initialize: function() {
            this.timer = setInterval(this.onTimer.bind(this), 1000);
            this.render();
        },

        onTimer: function() {
            if (--this.current <= 0) {
                clearTimeout(this.timer);
                this.trigger("elapsed");
            }
            this.render();
        },

        render: function() {
            var min = Math.floor(this.current / 60);
            var sec = this.current % 60;
            var str_min = '' + min;
            var str_sec = '' + sec;
            if (str_min < 10) str_min = '0' + min;
            if (str_sec < 10) str_sec = '0' + sec;

            this.$el.html(str_min + " : " + str_sec);
            return this;
        }
    });

    ExamNavigationView = Backbone.View.extend({
        events: {
            "click .top-nav .cell": "onTop",
            "click .center-nav .cell": "onCenter",
            "click .bottom-nav > div": "onBottom"
        },

        initialize: function() {
            this.prev = {top: 0, center: 0, bottom: 0};
            this.listenTo(this.model, "change:index", this.onChange);
            this.listenTo(this.model, "answer", this.onAnswer);
        },

        onTop: function(event) {
            var index = parseInt(event.currentTarget.id.substr(4));
            this.model.set("index", index * 10);
        },
        onCenter: function(event) {
            var index = parseInt(event.currentTarget.id.substr(4));
            this.model.set("index", this.prev.top * 10 + index);
        },
        onBottom: function(event) {
            var index = parseInt(event.currentTarget.id.substr(4));
            this.model.set("index", index);
        },

        onChange: function() {
            this.showActive(this.model.get("index"));
        },

        onAnswer: function(index) {
            this.$(".bottom-nav #rect" + index).addClass("answered");
        },

        showActive: function(index) {
            this.$(".top-nav .cell#rect" + this.prev.top).removeClass("active");
            this.$(".center-nav .cell#rect" + this.prev.center).removeClass("active");
            this.$(".bottom-nav #rect" + this.prev.bottom).removeClass("active");

            this.prev.top = Math.floor(index / 10);
            this.prev.center = index % 10;
            this.prev.bottom = index;

            this.$(".top-nav .cell#rect" + this.prev.top).addClass("active");
            this.$(".center-nav .cell#rect" + this.prev.center).addClass("active");
            this.$(".bottom-nav #rect" + this.prev.bottom).addClass("active");
        }
    });

    ExamQuestionView = Backbone.View.extend({
        events: {
            "click .answer-rect #true": "onTrue",
            "click .answer-rect #false": "onFalse"
        },

        initialize: function() {
            this.img_a_el = this.$("#image");
            this.img_el = this.img_a_el.find("img");
            this.num_el = this.$("#number #val");
            this.text_el = this.$("#text");
            this.text_translated_el = this.$("#text-lang");
            this.btt_true_el = this.$(".img-ans#true");
            this.btt_false_el = this.$(".img-ans#false");

            this.listenTo(this.model, "change:index", this.render);
        },

        onTrue: function() {
            this.model.setAnswer(true);
            this.renderAnswer();
        },
        onFalse: function() {
            this.model.setAnswer(false);
            this.renderAnswer();
        },

        renderAnswer: function() {
            var question = this.model.getCurrentQuestion();
            this.btt_true_el.removeClass("sel");
            this.btt_false_el.removeClass("sel");
            if (question.get("user_answer") == 1)
                this.btt_true_el.addClass("sel");
            else if (question.get("user_answer") == 0)
                this.btt_false_el.addClass("sel");
        },

        setImage: function(url) {
            if (url === undefined || url === null)
                this.img_a_el.hide();
            else {
                this.img_a_el.attr("href", url);
                this.img_a_el.css("background-image", "url(" + url + ")");
                this.img_a_el.show();
            }
        },

        render: function() {
            var question = this.model.getCurrentQuestion();
            var index = this.model.get("index");

            this.num_el.html(index + 1);
            this.text_el.html(question.get("text"));

            if (question.has("text_extra"))
                this.text_translated_el.html(question.get("text_extra"));
            else
                this.text_translated_el.empty();

            this.setImage(this.model.getCurrentQuestionImage());
            this.renderAnswer();
        }
    });

    ExamSummaryView = Backbone.View.extend({
        events: {
          "click": "hide"
        },
        initialize: function() {

        },

        show: function() {
            this.$el.show();
        },

        hide: function() {
            this.$el.hide();
        }
    });

    ExamView = Backbone.View.extend({
        events: {
            "click .control .summary": "onSummary",
            "click .control .buttons .btt-prev": "onPrev",
            "click .control .buttons .btt-next": "onNext"
        },

        constructor: function() {
            var params = arguments[0];

            this.model = new ExamModel({
                image_url: params.image_url,
                exam_url: params.exam_url,
                exam_id: params.exam.exam.id
            });
            this.model.questions.reset(params.exam.questions);

            this.msgbox = new MessageBox({el: params.msgbox_el});
            this.labels = params.labels;
            this.back_url = params.back_url;

            Backbone.View.prototype.constructor.apply(this, arguments);
        },

        initialize: function() {
            this.navigation = new ExamNavigationView({
                el: this.$(".exam-nav"),
                model: this.model
            });

            this.question = new ExamQuestionView({
                el: this.$(".exam-data"),
                model: this.model
            });

            this.timer = new ExamTimerView({
                el: this.$(".control .time #time"),
                total: 5 // total time in seconds
            });

            this.summary = new ExamSummaryView({
                el: this.$(".summarypanel"),
                model: this.model
            });

            this.listenTo(this.timer, "elapsed", this.onTimer);
            this.listenTo(this.model, "done", this.onDone);
            this.listenTo(this.model, "error:save", this.onModelSaveError);

            this.model.set("index", 0);
            this.$("a.cbox").colorbox();
        },

        onModelSaveError: function(response, ok_callback) {
            function close() {
                this.msgbox.hide();
            }
            this.msgbox.show({
                "text": this.labels.error_send,
                "icon": "glyphicon-remove-circle",
                "buttons": [
                    {
                        text: this.labels.btt_close, type: "btn-danger",
                        callback: close.bind(this)
                    },
                    {
                        text: this.labels.btt_try_again, type: "btn-primary",
                        icon: "glyphicon-repeat",
                        callback: this.onSummary.bind(this)
                    }
                ]
            });
        },

        onSummary: function() {
            this.model.set("can_answer", false);
            var self = this;
            this.model.sendCurrentAnswers(function() {
                window.location = self.back_url;
            });
//            this.summary.show();
        },
        onPrev: function() {
            this.model.showPrevious();
        },
        onNext: function() {
            this.model.showNext();
        },

        onTimer: function() {
//            this.model.set("can_answer", false);
//            this.summary.show();
        },
        onDone: function() {
//            this.summary.show();
        }
    });
})();
