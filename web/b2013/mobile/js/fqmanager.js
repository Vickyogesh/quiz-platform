/**
 * config keys:
 * - pageId: page selector.
 * - headerId: header selector. 
 */
function createExamQuestionManager(config) {
    var pg_id = config["pageId"];

    return {
        resizeTimer: null,
        pageId: config["pageId"],

        questionData: [],
        total_errors: 0,
        total_answers: 0,
        prev_index: -1,
        current_index: 0,

        header_el: $(config["headerId"]),
        grid_el: $(pg_id + " #qgrid"),
        image_el: $(pg_id + " #image"),
        txt_el: $(pg_id + " #txt"),

        // See cacheNextImages().
        _imgCache: [new Image(), new Image()],

        // Will be called before switching to another page.
        // By default do nothing.
        // See logout(), back().
        onLeave: function() {},

        // Handle guest access error.
        // See processError().
        onGuestLimit: function() {
            var self = this;
            $('<div>').simpledialog2({
                mode: 'button',
                headerText: "Errori",
                headerClose: false,
                // Guest's visits is exceeded. Access will be unlocked within 1 hr.
                buttonPrompt: "Numero di sessioni per utenti esterni esaurite. Si prega di ritornare tra un'ora.",
                buttons: {
                    'Ok': {'click': function() { self.logout(); }}
                }
            });
        },

        // Handle response error.
        processError: function(info) {
            var user = sessionStorage.getItem('quizutype');
            if (info.status == 403 && user == "guest")
                this.onGuestLimit();
            else
                aux_showError(info.description);
        },

        // Logout from the app.
        logout: function() {
            var self = this;
            window.name = null;
            aux_busy(true);
            $.ajax("/v1/authorize/logout").always(function() {
                self.onLeave();
                aux_deleteServicesCookies();
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
        getQuestions: function(onOk) {
            $.mobile.showPageLoadingMsg("b", "Attendere prego.");
            var self = this;
            var url = this.getQuestionsUrl();

            $.getJSON(url, function(info) {
                $.mobile.hidePageLoadingMsg();
                if (info.status != 200)
                    self.processError(info);
                else {
                    sessionStorage.setItem("examid", info.exam.id);
                    onOk.call(self, info.questions);
                }
            });
        },

        // Send answers list.
        // NOTE: you must provide sendAnswersUrl() function.
        sendAnswers: function(onOk, onError) {
            $.mobile.showPageLoadingMsg("b", "Attendere prego.");

            var id_list = [];
            var answer_list = [];
            var num = this.questionData.length;
            for (var i = 0; i < num; ++i) {
                var q = this.questionData[i];
                id_list.push(q.id);
                if (q.user_answer !== undefined)
                    answer_list.push(q.user_answer);
                else {
                    // set incorrect answer and increase errors counter.
                    answer_list.push(q.answer == 0 ? 1 : 0);
                    ++this.total_errors;
                }
            }

            var self = this;
            var url = this.sendAnswersUrl();
            var data = {questions: id_list, answers: answer_list};

            aux_postJSON(url, data, function(info) {
              $.mobile.hidePageLoadingMsg();
              if (info.status != 200) {
                if (onError === undefined)
                    self.processError(info);
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
            this.current_index = -1;
            this.prev_index = -1; // used in cacheNextImages()
            this.total_answers = 0;
            this.showNextQuestion();
        },

        // Build result `img` URL.
        // See showNextQuestion().
        buildImageUrl: function(img) {
            if (img != "")
              return "/img/" + img + ".jpg";
        },

        // Load images for next question(s) to show them faster.
        // See showNextQuestion().
        cacheNextImages: function() {
            function get_images_to_cache() {
                function fix(value, max) {
                    if (value >= max)
                        value = 0;
                    else if (value < 0)
                        value = max - 1;
                    return value;
                }
                var lst = [];
                var count = this.questionData.length;
                var forward = 
                    (this.prev_index == count - 1 && this.current_index == 0)
                    || (this.prev_index == 0 && this.current_index == 1)
                    || (this.prev_index != 0 && this.current_index > this.prev_index);

                var index = fix(this.current_index + 1, count);
                for (var i = 0; i < 2; ++i) {
                    lst.push(this.questionData[index].image);
                    index += (forward == true ? 1 : -1);
                    index = fix(index, count);
                }
                return lst;
            }

            var urls = get_images_to_cache.call(this);
            // First item in the `this.questionData` is a current question.
            // So we try to cache images strating form index 1.            
            var img;
            var start = this.current_index + 1;
            var end = Math.min(start + 2, this.questionData.length);
            var ci = 0;
            for (var i = start; i < end; i++) {
                img = this.buildImageUrl(this.questionData[i].image);
                if (img !== undefined)
                    this._imgCache[ci].src = img;
                ++ci;
            }
        },

        // Show next question in the list
        // (list of questions was received via getQuestions).
        showNextQuestion: function(jumpToUnanswered) {
            this.showQuestion(this.current_index + 1);
        },

        // Show previous question in the list.
        showPrevQuestion: function() {
            this.showQuestion(this.current_index - 1);
        },

        // Show question with the given index in the questionData list.
        showQuestion: function(index) {
            this.prev_index = this.current_index;
            this.current_index = index;

            if (this.current_index >= this.questionData.length)
                this.current_index = 0;
            else if (this.current_index < 0)
                this.current_index = this.questionData.length - 1;

            var info = this.current_index + 1;
            info = "(" + info + "/" + this.questionData.length + ")";
            this.header_el.html(info);

            var q = this.questionData[this.current_index];
            var image = this.buildImageUrl(q.image);

            this.setQuestion(q.id + ". " + q.text, q.answer, image);
            this.layout();
            this.cacheNextImages();

            // Set answer buttons state
            $(this.pageId + " #bttTrue").removeClass("active");
            $(this.pageId + " #bttFalse").removeClass("active");
            
            if (q.user_answer == 1)
                $(this.pageId + " #bttTrue").addClass("active");
            else if (q.user_answer == 0)
                $(this.pageId + " #bttFalse").addClass("active");
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

        // Save user answer for the current question.
        saveAnswer: function(answer) {
            var q = this.questionData[this.current_index];
            if (q.user_answer === undefined)
                ++this.total_answers;
            q.user_answer = answer;
            if (q.answer != q.user_answer)
                this.total_errors++;
        },

        // Set image and text position.
        layout: function() {
            this.grid_el.css("height", "");

            var p = this.grid_el.parent();
            var pw = p.width();
            var ph = p[0].clientHeight; //p.height();
            var h = ph - 20;

            var ch = p.children();
            for (var i = 0; i < ch.length; i++) {
                var el = ch[i];
                if (el != this.grid_el[0]) {
                    h -= el.clientHeight;
                }
            }

            aux_layoutGrid(this.pageId + " #qgrid");

            if (pw >= ph) { // horizontal
                this.image_el.css("height", h + "px");
                this.txt_el.css("height", "");

                if (this.image_el.css("background-image") == "none") {
                    this.image_el.parent().css("width", "0%");
                    this.txt_el.parent().css("width", "100%");
                }
                else {
                    this.image_el.parent().css("width", "30%");
                    this.txt_el.parent().css("width", "70%");
                }
                this.grid_el.css('height', h + 'px');
            }
            else { // vertical
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
                self.saveAnswer(1);
                if (self.total_answers == self.questionData.length)
                    self.sendAnswers();
                else
                    self.showNextQuestion();
            });
            $(this.pageId + " #bttFalse").click(function() {
                self.saveAnswer(0);
                if (self.total_answers == self.questionData.length)
                    self.sendAnswers();
                else
                    self.showNextQuestion();
            });
            $(this.pageId + " #bttSend").click(function() {
                // ci sono domande non risposte
                // Prosegui / Annulla (send/back)
                var has_questions = false;
                for (var i = 0; i < self.questionData.length; ++i) {
                    if (self.questionData[i].user_answer === undefined) {
                        has_questions = true;
                        break;
                    }
                }
                if (has_questions) {
                    $('<div>').simpledialog2({
                        mode: 'button',
                        headerText: "Info",
                        headerClose: false,
                        // There are unanswered questions.
                        buttonPrompt: "Ci sono domande non risposte",
                        buttons: {
                            'Prosegui': {click: function() { self.sendAnswers(self.showNumErrors); }},
                            'Annulla': {click: function() {}, icon: "delete"}
                        }
                    });
                }
                else
                self.sendAnswers(self.showNumErrors);
            });

            $(this.pageId + " #bttPrevQ").click(function() {
                self.showPrevQuestion();
            });
            $(this.pageId + " #bttNextQ").click(function() {
                self.showNextQuestion();
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
