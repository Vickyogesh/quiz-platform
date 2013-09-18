/**
 * config keys:
 * - pageId: page selector.
 * - headerId: header selector. 
 */
function createQuestionManager(config) {
    var pg_id = config["pageId"];

    return {
        resizeTimer: null,
        pageId: config["pageId"],

        questionData: [],
        current_ids: [],
        current_answers: [],
        total_errors: 0,
        num_questions: 0,

        header_el: $(config["headerId"]),
        grid_el: $(pg_id + " #qgrid"),
        image_el: $(pg_id + " #image"),
        txt_el: $(pg_id + " #txt"),

        onLeave: function() {},

        // Logout from the app.
        logout: function() {
            var self = this;
            window.qsid = null;
            window.name = null;
            aux_busy(true);
            $.ajax("/v1/authorize/logout").always(function() {
                self.onLeave();
                aux_busy(false);
                $.mobile.changePage("#page-login");
            });
        },

        // Back to main (or previous) screen.
        // By default return to main screen.
        back: function() {
            this.onLeave();
            $.mobile.changePage("#page-student",
                                {transition: "slide", reverse: true});
        },

        // Get list of questions.
        // NOTE: you must provide getQuestionsUrl(force) function.
        getQuestions: function(onOk, force) {
            $.mobile.showPageLoadingMsg("b", "Attendere prego.");
            var self = this;
            var url = this.getQuestionsUrl(force);

            $.getJSON(url, function(info) {
                $.mobile.hidePageLoadingMsg();
                if (info.status != 200)
                    aux_showError(info.description);
                else
                    onOk.call(self, info.questions);
            });
        },

        // Send answers list.
        // NOTE: you must provide sendAnswersUrl() function.
        sendAnswers: function(onOk, onError) {
            if (this.current_ids.length == 0) {
                if (onError !== undefined)
                    onError.call(this);
                return;
            }

            $.mobile.showPageLoadingMsg("b", "Attendere prego.");

            var self = this;
            var url = this.sendAnswersUrl();
            var data = {
                questions: this.current_ids,
                answers: this.current_answers
            };

            this.current_ids = [];
            this.current_answers = [];

            aux_postJSON(url, data, function(info) {
              $.mobile.hidePageLoadingMsg();
              if (info.status != 200) {
                if (onError === undefined)
                  aux_showError(info.description);
                else
                  onError.call(self, info);
              }
              else if (onOk !== undefined)
                onOk.call(self, info);
            });
        },

        // Set list of received questions.
        setQuestions: function(questions) {
            this.total_errors = 0;
            this.questionData = questions;
            this.num_questions = this.questionData.length;
            this.showNextQuestion();
        },

        // Show next question (list of questions was received via getQuestions).
        // If question list is empty then ask more questions.
        showNextQuestion: function() {
            // Ask more.
            if (this.questionData.length == 0) {
                this.sendAnswers(function() {
                    this.getQuestions(this.setQuestions);
                });
                return;
            }

            var info = this.num_questions - this.questionData.length + 1;
            info = "(" + info + "/" + this.num_questions + ")";
            this.header_el.html(info);

            var q = this.questionData[0];
            var image;
            if (q.image != "")
              image = "/img/" + q.image + ".jpg";

            this.setQuestion(q.id + ". " + q.text, q.answer, image);
            this.layout();
        },

        // Set question text and optionally image.
        setQuestion: function(text, answer, img) {
            this.txt_el.html(text);
            this.txt_el.attr("answer", answer);

            if (img === undefined || img == "")
                this.image_el.css("background-image", "none");
            else
                this.image_el.css("background-image", "url('"+ img + "')");
        },

        // Save user answer and remove question from the list.
        saveAnswer: function(answer) {
            var q = this.questionData.shift();
            if (q.answer != answer)
                this.total_errors++;
            this.current_ids.push(q.id);
            this.current_answers.push(answer);
        },

        // Set image and text position.
        layout: function() {
            var p = this.grid_el.parent();
            var pw = p.width();
            var ph = p.height();

            aux_layoutGrid(this.pageId + " #qgrid");

            if (pw >= ph) { // horizontal
                this.image_el.css("height", "");
                this.txt_el.css("height", "");

                if (this.image_el.css("background-image") == "none") {
                    this.image_el.parent().css("width", "0%");
                    this.txt_el.parent().css("width", "100%");
                }
                else {
                    this.image_el.parent().css("width", "30%");
                    this.txt_el.parent().css("width", "70%");
                    this.image_el.css(
                        "height",
                        Math.min(200,this.image_el.parent().height())
                    );
                }
            }
            else { // vertical
              var h = ph - 30;
              var ih = Math.min(200, h / 3);
              var th = h - ih;

              this.image_el.parent().css("width", "");
              this.image_el.parent().css("height", ih + "px");
              this.image_el.css("height", ih + "px");
              
              this.txt_el.parent().css("width", "");
              this.txt_el.css("height", th + "px");
            }
        },

        showNumErrors: function() {
            aux_showError('Fatto! Hai commesso '
                          + this.total_errors + ' errori.',
                          'Info');
            this.total_errors = 0;
        },

        // Init manager.
        init: function() {
            var self = this;

            $(this.pageId + " #bttLogout").click(function() {
                self.sendAnswers(self.logout, self.logout);
            });

            $(this.pageId + " #bttBack").click(function() {
                self.sendAnswers(self.back, self.back);
            });

            $(this.pageId + " #bttTrue").click(function() {
                if (self.questionData.length > 0) {
                    self.saveAnswer(1);
                    self.showNextQuestion();
                }
            });
            $(this.pageId + " #bttFalse").click(function() {
                if (self.questionData.length > 0) {
                    self.saveAnswer(0);
                    self.showNextQuestion();
                }
            });
            $(this.pageId + " #bttSend").click(function() {
                if (self.questionData.length == 0)
                    return;
                self.sendAnswers(self.showNumErrors);
            });

            $(this.pageId).bind('pagebeforeshow', function() {
                self.image_el.css("background-image", "");
                self.txt_el.html("");
                self.header_el.html("");
            });

            $(this.pageId).bind('orientationchange', function() {
                self.layout();
            });

            $(this.pageId).bind('pageshow', function() {
                self.getQuestions(self.setQuestions);
                self.layout();
            });

            $(window).resize(function() {
                clearTimeout(self.resizeTimer);
                self.resizeTimer = setTimeout(function() {
                    self.layout();
                }, 100);
            });
        } // init
    } // return
} // createQuestionManager
