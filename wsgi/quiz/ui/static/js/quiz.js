(function() {
    function get_row_obj(sel) {
        var el = $(sel);
        return {
          cells_el: el.find("> div"),
          text: el.find("#text").first(),
          btt_true: el.find(".img-ans.true").first(),
          btt_false: el.find(".img-ans.false").first(),
          ansbox: el.find(".ansbox").first()
        };
    }

    Quiz = function () {
        var self = this;
        this.questions = null;
        this.topic = 0;
        this.index = 0;
        this.last_answered_index = -1;
        this.can_answer = true;
        this.is_show_answers = false;
        this.is_can_load_more = true;
        this.total_errors = 0;

        this.img_preload = new Image();
        this.image_a_el = $("#question_image");
        this.image_el = this.image_a_el.find("img").first();
        this.image_url_fmt = window.g.image_url + "%s.jpg";

        this.rows = [
            get_row_obj("#row0"),
            get_row_obj("#row1"),
            get_row_obj("#row2"),
            get_row_obj("#row3"),
            get_row_obj("#row4")
        ];

        // Set question image and optional next image for preloading.
        // If img_name is invalid then hide image.
        this.set_image = function(img_name, next_img_name) {
            if (img_name === "" || img_name === null || img_name === undefined)
                self.image_a_el.hide();
            else {
                var url = sprintf(self.image_url_fmt, img_name);
                self.image_el.attr("src", url);
                self.image_a_el.attr("href", url);
                self.image_a_el.show();
            }
            if (next_img_name !== "" && next_img_name !== null && next_img_name !== undefined)
                self.img_preload.src = sprintf(self.image_url_fmt, next_img_name);
        };

        // Show next question in the list or do nothing if end is reached.
        this.show_next_question = function() {
            if (self.index <= self.last_answered_index) {
                if (self.index + 1 < self.questions.length) {
                    ++self.index;
                    self.show_question(self.index);
                }
            }
        };

        // Show previous questionin the list or skip if start is reached.
        this.show_prev_question = function() {
            if (self.index > 0) {
                --self.index;
                self.show_question(self.index);
            }
        };

        // Helper func.
        // Show answer (change true or false button class) and display
        // state of the answer (correct/incorrect) if required.
        // Used by _set_question().
        this._show_answer = function(row, question) {
            var answer = question && question.user_answer;

            row.ansbox.removeClass("correct");
            row.ansbox.removeClass("incorrect");
            if (answer !== undefined) {
                if (answer == 1) {
                    row.btt_true.addClass("sel");
                    row.btt_false.removeClass("sel");
                }
                else {
                    row.btt_true.removeClass("sel");
                    row.btt_false.addClass("sel");
                }
                if (self.is_show_answers) {
                    row.ansbox.addClass(question.answer == answer
                        ? "correct" : "incorrect");
                }
            }
            else {
                row.btt_true.removeClass("sel");
                row.btt_false.removeClass("sel");
            }
        };

        // Helper func.
        // Set question text and answer for the given row
        // and question data. If data is invalid then hide the row.
        // Used by show_question().
        this._set_question = function(row_index, question) {
            var row = self.rows[row_index];
            if (question === undefined) {
                row.cells_el.addClass("hidden");
                row.text.html("");
                row.btt_true.hide();
                row.btt_false.hide();
            }
            else {
                row.cells_el.removeClass("hidden");
                row.text.html(question.text);
                row.btt_true.show();
                row.btt_false.show();
                self._show_answer(row, question);
            }
        };

        // Show question for the given index and also
        // 2 previous question and 2 next questions if possible.
        // Also show active question image.
        this.show_question = function(index) {
            var i, q;
            // fill first two rows
            for (i = index - 2; i < index; ++i) {
                q = self.questions[i];
                self._set_question(i - index + 2, q);
            }
            // fill last two rows
            for (i = index + 1; i <= index + 2; ++i) {
                q = self.questions[i];
                self._set_question(i - index + 2, q);
            }
            // fill active question
            q = self.questions[index];
            // 2 - index of the row with active question.
            // See self.rows and get_row_obj().
            self._set_question(2, q);

            // Next image to load.
            var next = self.questions[index + 1];
            if (next !== undefined)
                next = next.image;

            self.set_image(q.image, next);
        };

        // Update show answers state - redraws rows.
        this.show_answers = function(state) {
            if (self.is_show_answers == state)
                return;
            self.is_show_answers = state;
            self.show_question(self.index);
        };

        // Set answer for the current question and move to next one.
        this.set_current_answer = function (answer) {
            var q = self.questions[self.index];
            if (q.user_answer === undefined) {
                q.user_answer = answer;
                self.last_answered_index = self.index;

                if (q.answer != q.user_answer)
                    ++self.total_errors;

                // End of question list is reached
                if (self.index == self.questions.length - 1) {
                    self.show_question(self.index);
                    self.send_answers(self.show_done);
                    return;
                }

                self.show_next_question();
                if (self.index + 3 >= self.questions.length)
                    self.load_more_questions();
            }
        };

        // Send answers and call 'callback' function on success.
        // On error show message box with error info, cancel and retry buttons.
        // Retry will call send_answers() again.
        // It also marks questions as sent.
        this.send_answers = function(callback, data) {
            if (data === undefined) {
                var ids = [];
                var answers = [];
                var sent_questions = [];

                for (var i in self.questions) {
                    var q = self.questions[i];
                    if (q.user_answer !== undefined && q.sent != true) {
                        ids.push(q.id);
                        sent_questions.push(i);
                        answers.push(q.user_answer);
                    }
                }

                data = {questions:ids, answers:answers};
            }

            function on_send() {
                for (var i in sent_questions) {
                    var q = self.questions[sent_questions[i]];
                    q.sent = true;
                }
                callback();
            }

            // Seems all answers already sent, so just run callback.
            if (data.questions.length == 0) {
                callback();
                return;
            }

            var url = window.g.quiz_url + self.topic;

            Aux.postJson(url, data, on_send).error(function(response) {
                self.show_error(response, window.g.error_msg_send, function() {
                    self.send_answers(callback, data);
                });
            });
        };

        this.show_error = function(response, main_message, retry_callback) {
            self.error_box.set_text(main_message);
            self.error_box.on("tryagain", function() {
                self.error_box.show(false);
                retry_callback();
            });
            self.error_box.show();
        };

        // Set initial questions or append new ones to the end of list.
        // If data is empty then no more questions can be asked from backend
        // (it always will return zero list until 'force' query).
        // If show_done_on_empty is true then on empty data done message
        // will be shown.
        this.set_questions = function(data, show_done_on_empty) {
            self.topic = data.topic;
            if (data.questions.length == 0) {
                if (show_done_on_empty == true) {
                    self.questions = [];
                    self.show_done();
                }
                else
                    self.is_can_load_more = false;
            }
            else {
                if (self.questions === null)
                    self.questions = data.questions;
                else
                    self.questions = self.questions.concat(data.questions);
                self.show_question(self.index);
            }
        };

        // Load more questions excluding already loaded and answered ones.
        // If force is true then quiz will be reset (all answers will be
        // marked as not answered).
        this.load_more_questions = function(force) {
            if (!self.can_answer || !self.is_can_load_more)
                return;
            var exclude = [];
            var params = {};
            var url = window.g.quiz_url + self.topic;

            // Build list of not answered questions to prevent duplicates.
            for(var i in self.questions) {
                var q = self.questions[i];
                if (q.sent != true)
                    exclude.push(q.id);
            }

            if (exclude.length != 0)
                params.exclude = exclude.toString();
            if (force == true)
                params.force = true;

            params = decodeURIComponent($.param(params));
            if (params.length != 0)
                url += "?" + params;

            $.getJSON(url, function(data) {
                self.set_questions(data);
            }).error(function(response) {
                self.show_error(response, window.g.error_msg_get, function() {
                    self.load_more_questions(force);
                });
            });
        };

        this.show_done = function() {
            var txt;
            if (self.questions.length != 0) {
                txt = sprintf(window.g.msg_done_info, {errors:self.total_errors});
                txt = window.g.msg_done + "<br>" + txt;
                $("#done_box #review").show();
            }
            else {
                txt = window.g.msg_done;
                $("#done_box #review").hide();
            }
            self.done_box.set_text(txt);
            self.done_box.show();
        };

        this.init = function(data) {
            // Done dialog box
            self.done_box = new MessageLayer("#quiz-content", "done_box");
            self.done_box.on_show = function() {
                $("#btt-done").hide();
                $("#navbar label").attr("disabled", "true");
            };
            self.done_box.on_hide = function() {
                $("#btt-done").show();
                $("#navbar label").removeAttr("disabled");
            };
            self.done_box.set_icon("glyphicon-ok-circle");
            self.done_box.set_text(window.g.msg_done);
            self.done_box.add_button("btn-success", "glyphicon-arrow-left",
                "back", window.g.msg_btt_back, function() {
                    window.location = window.g.back_url;
                }
            );
            self.done_box.add_button("btn-primary", "glyphicon-repeat",
                "reload", window.g.msg_btt_restart, function() {
                    self.done_box.show(false);
                    self.load_more_questions(true);
                }
            );
            self.done_box.add_button("btn-default", "glyphicon-eye-open",
                "review", window.g.msg_btt_review, function() {
                    self.can_answer = false;
                    self.done_box.show(false);
                }
            );

            // Error dialog box.
            self.error_box = new MessageLayer("#quiz-content", "error_box");
            self.error_box.on_show = self.done_box.on_show;
            self.error_box.on_hide = self.done_box.on_hide;
            self.error_box.set_icon("glyphicon-remove-circle");
            self.error_box.add_button("btn-danger", "",
                "close", window.g.msg_btt_close, function() {
                    self.error_box.show(false);
                }
            );
            self.error_box.add_button("btn-primary", "glyphicon-repeat",
                "tryagain", window.g.msg_btt_try_again);

            // Info box
            self.info_box = new MessageLayer("#quiz-content", "info_box");
            self.info_box.on_show = self.done_box.on_show;
            self.info_box.on_hide = self.done_box.on_hide;
            self.info_box.add_button("btn-success", "glyphicon-arrow-left",
                "back", window.g.msg_btt_back, function() {
                    window.location = window.g.back_url;
                }
            );
            self.info_box.add_button("btn-default", "glyphicon-eye-open",
                "review", window.g.msg_btt_quiz_back, function() {
                    self.info_box.show(false);
                }
            );


            $("#quiz-content").mousewheel(function(event) {
                if (event.deltaY > 0)
                    self.show_prev_question();
                else if (event.deltaY < 0)
                    self.show_next_question();
            });

            var row = self.rows[2];
            row.btt_true.click(function() {
                if (!self.can_answer)
                    return;
                self.set_current_answer(1);
            });
            row.btt_false.click(function() {
                if (!self.can_answer)
                    return;
                self.set_current_answer(0);
            });

            $("form.navbar-form").change(function() {
               self.show_answers(($(this).find("#opt_yes").prop("checked")));
            });

            $("#btt-done").click(function() {
                self.send_answers(function() {
                    var txt = sprintf(window.g.msg_done_info, {errors:self.total_errors});
                    self.info_box.set_text(txt);
                    self.info_box.show();
                });
            });

            self.set_questions(data, true);
        };
    }
})();
