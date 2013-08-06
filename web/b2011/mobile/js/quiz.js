$("#page-quiz").bind("pageinit", function() {
  var info_el = $("#page-quiz .ui-header h3 > span");
  var quizData = [];
  var current_ids = [];
  var current_answers = [];
  var total_errors = 0;
  var num_questions = 0;
  
  function setQuestion(text, answer, img) {
    var image = $("#page-quiz #image");
    var txt = $("#page-quiz #txt");

    txt.html(text);
    txt.attr("answer", answer);

    if (img === undefined || img == "")
      image.css("background-image", "none");
    else
      image.css("background-image", "url('"+ img + "')");
  }

  function layout() {
    var image = $("#page-quiz #image");
    var txt = $("#page-quiz #txt");
    
    var grid = $("#qgrid");
    var p = grid.parent();
    var pw = p.width();
    var ph = p.height();

    aux_layoutGrid("#qgrid");

    if (pw >= ph) { // horizontal
      image.css("height", "");
      txt.css("height", "");

      if (image.css("background-image") == "none") {
        image.parent().css("width", "0%");
        txt.parent().css("width", "100%");
      }
      else {
        image.parent().css("width", "30%");
        txt.parent().css("width", "70%");
        image.css("height", Math.min(200, image.parent().height()));
      }
    }
    else { // vertical
      var h = ph - 30;
      var ih = Math.min(200, h / 3);
      var th = h - ih;

      image.parent().css("width", "");
      image.parent().css("height", ih + "px");
      image.css("height", ih + "px");
      
      txt.parent().css("width", "");
      txt.css("height", th + "px");
    }
  }

  function showNextQuestion() {
    if (quizData.length == 0)
    {
      sendQuiz(function() {
        getQuiz(setQuestions);
      });
      return;
    }

    var info = num_questions - quizData.length + 1;
    info = "(" + info + "/" + num_questions + ")";
    info_el.html(info);

    var q = quizData[0];
    var image;
    if (q.image != "")
      image = "/img/" + q.image + ".jpg";

    setQuestion(q.id + ". " + q.text, q.answer, image);
    layout();
  }

  function pushAnswer(answer) {
    var q = quizData.shift();
    if (q.answer != answer)
      total_errors++;
    current_ids.push(q.id);
    current_answers.push(answer);
  }

  function getQuiz(on_ok, force) {
    $.mobile.showPageLoadingMsg("b", "Attendere prego.");
    var topic = sessionStorage.getItem("topic");
    var url = "/v1/quiz/" + topic;

    if (force == true)
      url += "?force=true";

    $.getJSON(url, function(info) {
      $.mobile.hidePageLoadingMsg();
      if (info.status != 200)
          aux_showError(info.description);
      else
          on_ok(info.questions);
    });    
  }

  function setQuestions(questions) {
    if (questions.length == 0) {
      $('<div>').simpledialog2({
        mode: 'button',
        headerText: "Quiz",
        headerClose: false,
        buttonPrompt: "Hai risposto a tutte le domande di questo argomento! Continuare comunque?",
        buttons: {
          'Ok': {'click': function () {
            getQuiz(setQuestions, true);
          }},
          'Cancel': {'click': function () {}, icon: "delete", theme: "c"}
        }
      });
    }
    else {
      quizData = questions;
      num_questions = quizData.length;
      showNextQuestion();
    }
  }

  function sendQuiz(on_ok, on_error) {
    if (current_ids.length == 0) {
      if (on_error !== undefined)
        on_error();
      return;
    }

    $.mobile.showPageLoadingMsg("b", "Attendere prego.");
    var url = "/v1/quiz/" + sessionStorage.getItem("topic");

    var data = {questions: current_ids, answers: current_answers};
    current_ids = [];
    current_answers = [];

    aux_postJSON(url, data, function(info) {
      $.mobile.hidePageLoadingMsg();
      if (info.status != 200) {
        if (on_error === undefined)
          aux_showError(info.description);
        else
          on_error(info);
      }
      else if (on_ok !== undefined)
        on_ok(info);
    });
  }

  $("#page-quiz").bind('pagebeforeshow', function() {
    $("#page-quiz #image").css("background-image", "");
    $("#page-quiz #txt").html("");
  });
  $("#page-quiz").bind('orientationchange', function() {
      layout();
  });
  $("#page-quiz").bind('pageshow', function() {
    getQuiz(setQuestions);
    layout();
  });

  var resizeTimer;
  $(window).resize(function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function(){ layout(); }, 100);
  });

  $("#page-quiz #bttQuizTrue").click(function() {
    if (quizData.length > 0) {
      pushAnswer(1);
      showNextQuestion();
    }
  });
  $("#page-quiz #bttQuizFalse").click(function() {
    if (quizData.length > 0) {
      pushAnswer(0);
      showNextQuestion();
    }
  });
  $("#page-quiz #bttQuizSend").click(function() {
    if (quizData.length > 0)
      sendQuiz(function(argument) {
        aux_showError('Fatto! Hai commesso ' + total_errors + ' errori.');
        total_errors = 0;
      });
  });

  $("#page-quiz #bttLogout").click(function() {
    function logout() {
      window.qsid = null;
      window.name = null;
      aux_busy(true);
      $.ajax("/v1/authorize/logout").always(function() {
          aux_busy(false);
          $.mobile.changePage("#page-login");
      });
    }
    sendQuiz(logout, logout);
  });

  $("#page-quiz #bttBack").click(function() {
    function back() {
      $.mobile.changePage("#page-quiz-topics",
                          {transition: "slide", reverse: true});
    }
    sendQuiz(back, back);
  });

});
