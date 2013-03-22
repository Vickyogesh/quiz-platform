/*********************************************************
** AUX tools.
*********************************************************/

function get_arg_prefix(url)
{
    if (url.indexOf('?') == -1)
      return "?";
    else
      return "&";
}
//----------------------------------------------------------------------------

function url(url)
{
  var path = url;

  // NOTE: uncomment if you want cross domain requests
  // var server = "http://127.0.0.1"
  // var server = "https://quizplatformtest-editricetoni.rhcloud.com"
  // var server = "http://quizplatform-editricetoni.rhcloud.com"
  // path = server + url;
  // if (window.qsid)
  //   path += get_arg_prefix(path) + "sid=" + window.qsid;

  return path;
}
//----------------------------------------------------------------------------

// Convert ISO date string YYYY-MM-DDTHH:MM:SS to JS Date object
function aux_dateFromISO(iso_time)
{
  MM = ["Jan", "Feb","Mar","Apr","May","Jun","Jul",
        "Aug","Sep","Oct","Nov", "Dec"];

  iso_time += ' UTC';
  var expires = iso_time.replace(
      /(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})/,
      function($0,$1,$2,$3,$4,$5,$6){
          return $3 + " " + MM[$2-1] + " " + $1 + " " + $4 + ":" +$5 + ":" + $6;
      }
  )

  var d = new Date();
  d.setTime(Date.parse(expires))
  return d;
}
//----------------------------------------------------------------------------

// Show error dialog
function aux_showError(msg, code)
{
  $("#msg .modal-header h3").html('Error: ' + code);
  $("#msg .modal-body").html(msg)
  $("#msg").modal('show')
}
//----------------------------------------------------------------------------

function aux_showJSONError(data)
{
  aux_showError(data.description, data.status)
}
//----------------------------------------------------------------------------

// Show info label for the specified tab
function aux_showInfo(tab)
{
  var label = tab.find("#infoLabel");
  label.fadeIn().delay(800).fadeOut();
}
//----------------------------------------------------------------------------

// Hide features and show login dialog
function aux_showLogin()
{
  $("#features").hide();
  $(".form-signin").show();
}
//----------------------------------------------------------------------------

// Hide login dialog and show features
function aux_showFeatures()
{
  $(".form-signin").hide();
  $("#features").show();
}
//----------------------------------------------------------------------------

// Uncheck questions in the specified table
function aux_deselect(tbl)
{
  tbl.find("thead input").attr("checked", false);
  tbl.find("tbody input").each(function(){
    this.checked = false;
  })
}
//----------------------------------------------------------------------------

// Fill tbl with the questions
function aux_fillTable(tbl, questions)
{
  var body = tbl.find("tbody");
  body.find("tr").remove();

  var answer = false;
  for (var i = 0; i < questions.length; i++)
  {
    answer = questions[i].answer;

    var html = "<tr>";
    html += "<td>" + (i + 1) + ".</td>";
    html += "<td>(" + questions[i].id +") "+ questions[i].text + "</td>";
    html += "<td>" + (answer ? "true":"false") + "</td>";
    html += "<td><input type='checkbox' value='" + questions[i].id +"'/></td>";

    body.append(html);
  }
}
//----------------------------------------------------------------------------

function onSelectAllQuestions()
{
  var state = this.checked;
  $(this).parents("table").find("tbody input").each(function(){
    this.checked = state;
  })
}
//----------------------------------------------------------------------------

// Remove session cookie, hide features and show login dialog
function doQuit()
{
  window.qsid = null;
  aux_showLogin();
}
//----------------------------------------------------------------------------

function aux_postJSON(url, data, success)
{
  $.ajax({
    url: url,
    type: "POST",
    contentType: "application/json; charset=UTF-8",
    data: JSON.stringify(data),
    dataType: "json",
    success: success
  });
}
//----------------------------------------------------------------------------


/*********************************************************
** Event handlers.
*********************************************************/

function onAuth()
{
  $.getJSON(url("/v1/authorize"), function(data) {
    // Calculate digest
    var login = $(".form-signin #login").val();
    var passwd = $(".form-signin #pass").val();
    var nonce = data.nonce;
    var digest = hex_md5(login + ':' + passwd);

    var auth = {
      nonce: nonce,
      username: login,
      appid: "32bfe1c505d4a2a042bafd53993f10ece3ccddca",
      digest: hex_md5(nonce + ':' + digest)
    };

    // Now we can send authorization data
    aux_postJSON(url("/v1/authorize"), auth, function (data) {
      if (data.status != 200) {
        doQuit();
        aux_showError("Authorization is not passed.", data.status);
      }
      else {
        window.qsid = data.sid;
        aux_showFeatures();
      }
    });

  }); // GET
}
//----------------------------------------------------------------------------

function onGetQuiz()
{
  $("#quiztab table thead input").attr("checked", false);

  var topic = $("#quiztab #topic").val();
  var lang = $("#quiztab #lang").val();
  var uri = url("/v1/quiz/" + topic);
  var data = {}
  
  if (lang != "it")
    data.lang = lang;

  $.getJSON(uri, data, function(data) {
    if (data.status != 200)
      aux_showJSONError(data);
    else
      aux_fillTable($("#quiztab table"), data.questions);
  });
}
//----------------------------------------------------------------------------

function onSendQuiz()
{
  var topic = $("#quiztab #topic").val();
  var lst = $("#quiztab table tbody input");
  var id_list = [];
  var answer_list = [];

  $("#quiztab table tbody input").each(function(i){
    id_list.push(this.value);
    answer_list.push(this.checked ? 1 : 0);
  });

  var data = {
    questions: id_list,
    answers: answer_list
  };

  aux_postJSON(url("/v1/quiz/" + topic), data, function (data) {
    if (data.status != 200)
      aux_showJSONError(data);
    else
    {
      aux_deselect($("#quiztab table"));
      aux_showInfo($("#quiztab"), "Done!");
    }
  });
}
//----------------------------------------------------------------------------

function onGetExam()
{
  var lang = $("#examtab #lang").val();
  var data = {}

  if (lang != "it")
    data.lang = lang;

  $.getJSON(url("/v1/exam"), data, function(data) {
    if (data.status != 200)
      aux_showJSONError(data);
    else
    {
      $("#examtab #examid").attr("exam", data.exam.id);
      var expires = aux_dateFromISO(data.exam.expires);
      $("#examtab h4").text("Exam expires at: " + expires.toLocaleString());
      aux_fillTable($("#examtab #examtable"), data.questions);
    }
  });
}
//----------------------------------------------------------------------------

function onSendExam()
{
  var id_list = [];
  var answer_list = [];

  $("#examtab table tbody input").each(function(i){
    id_list.push(this.value);
    answer_list.push(this.checked ? 1 : 0);
  });

  var id = $("#examtab #examid").attr("exam");
  var data = {
    questions: id_list,
    answers: answer_list
  }

  aux_postJSON(url("/v1/exam/" + id), data, function (data) {
    if (data.status != 200)
      aux_showJSONError(data);
    else
    {
      aux_deselect($("#examtab table"));
      aux_showInfo($("#examtab"), "Done!");
    }
  });
}
//----------------------------------------------------------------------------


function onGetReview()
{
  $("#reviewtab table thead input").attr("checked", false);

  var lang = $("#reviewtab #lang").val();
  var uri = url("/v1/errorreview");
  var data = {}

  if (lang != "it")
    data.lang = lang;

  $.getJSON(uri, data, function(data) {
    if (data.status != 200)
      aux_showJSONError(data);
    else
      aux_fillTable($("#reviewtab table"), data.questions);
  });
}
//----------------------------------------------------------------------------

function onSendReview()
{
  var lst = $("#reviewtab table tbody input");
  var id_list = [];
  var answer_list = [];

  $("#reviewtab table tbody input").each(function(i){
    id_list.push(this.value);
    answer_list.push(this.checked ? 1 : 0);
  });

  var data = {
    questions: id_list,
    answers: answer_list
  };

  aux_postJSON(url("/v1/errorreview"), data, function (data) {
    if (data.status != 200)
      aux_showJSONError(data);
    else
    {
      aux_deselect($("#reviewtab table"));
      aux_showInfo($("#reviewtab"), "Done!");
    }
  });
}
//----------------------------------------------------------------------------

function aux_clearUserStat()
{
  $("#studentstattab .row #id").text('N/A');
  $("#studentstattab .row #name").text('N/A');
  $("#studentstattab .row #exams").text('N/A');
  $("#studentstattab tbody tr").remove();
}
//----------------------------------------------------------------------------

function aux_fillUserStat(data)
{
  var html = "";
  var body = $("#studentstattab tbody");

  $("#studentstattab .row #id").text(data.student.id);
  $("#studentstattab .row #name").text(data.student.name + ' ' + data.student.surname);

  if (data.exams.length)
  {
    var exams = data.exams;
    for (var i in exams)
    {
      var exam = exams[i];
      var status = exam.status

      if (status == "expired" || status > 4)
        html += "<span class='label label-important'>&nbsp;";
      else
        html += "<span class='label label-success'>&nbsp;";
      html += status + '&nbsp;</span>&nbsp;';
    }

    $("#studentstattab .row #exams").html(html);
  }

  var topics = data.topics;
  for (var t in topics)
  {
    html = "<tr>";
    html += "<td>" + topics[t].id + ".</td>";
    html += "<td>" + topics[t].text + "</td>";

    var err = topics[t].errors;

    if (err == -1)
      html += "<td>" + "<span class='label label-important'>Not enough exercises</span></td>";
    else if (err >= 20 )
      html += "<td>" + "<span class='badge badge-important'>" + err + "%</span></td>";
    else if (err > 0)
      html += "<td>" + "<span class='badge badge-warning'>" + err + "%</span></td>";
    else
      html += "<td>" + "<span class='badge badge-success'>" + err + "%</span></td>";

    body.append(html);
  }
}
//----------------------------------------------------------------------------

function onStudentStat()
{
  var user_id = $("#studentstattab #id").val();
  var lang = $("#studentstattab #lang").val();
  var data = {}
  if (lang != "it")
    data.lang = lang;

  aux_clearUserStat();

  $.getJSON(url("/v1/student/"+user_id), data, function(data) {
    aux_fillUserStat(data);
  })
  .error(function(data) {
    aux_showError(data.responseText, data.status);
  });
}
//----------------------------------------------------------------------------

function aux_clearExamList()
{
  $("#examlisttab .row #id").text('N/A');
  $("#examlisttab .row #name").text('N/A');
  $("#examlisttab tbody tr").remove();
}
//----------------------------------------------------------------------------

function aux_fillExamList(data)
{
  var html = "";
  var body = $("#examlisttab tbody");

  $("#examlisttab .row #id").text(data.student.id);
  $("#examlisttab .row #name").text(data.student.name + ' ' + data.student.surname);

  var exams = data.exams;
  for (var t in exams)
  {
    var exam = exams[t]
    var start_time = aux_dateFromISO(exam.start).toLocaleString();
    var end_time = aux_dateFromISO(exam.end).toLocaleString();
    html = "<tr>";
    html += "<td>" + exam.id + ".</td>";
    html += "<td>" + start_time + "</td>";

    if (exam.status == "expired")
      html += "<td colspan='2'><span class='badge badge-important'>expired</span></td>";
    else if (exam.status == "in-progress")
      html += "<td colspan='2'><span class='badge badge-info'>in progress</span></td>";
    else
    {
      html += "<td>" + end_time + "</td>";
      if (exam.status == "passed")
        html += "<td><span class='badge badge-success'>";
      else
        html += "<td><span class='badge badge-important'>";
      html += exam.errors + "</span></td>";
    }
    body.append(html);
  }
}
//----------------------------------------------------------------------------

function onStudentExams()
{
  var user_id = $("#examlisttab #id").val();

  aux_clearExamList();

  $.getJSON(url("/v1/student/"+user_id+"/exam"), function(data) {
    if (data.status != 200)
      aux_showJSONError(data);
    else
      aux_fillExamList(data);
  })
  .error(function(data) {
    aux_showError(data.responseText, data.status);
  });
}
//----------------------------------------------------------------------------

function onExamInfo()
{
  var exam_id = $("#examinfotab #id").val();
  var lang = $("#examinfotab #lang").val();
  var data = {}
  
  if (lang != "it")
    data.lang = lang;

  $.getJSON(url("/v1/exam/"+exam_id), data, function(data) {
    if (data.status != 200)
      aux_showJSONError(data);
    else
      aux_fillExamInfo(data);
  })
  .error(function(data) {
    aux_showError(data.responseText, data.status);
  });
}
//----------------------------------------------------------------------------

function timestring(data)
{
  return aux_dateFromISO(data).toLocaleString();
}
//----------------------------------------------------------------------------

function aux_fillExamInfo(data)
{
  var exam = data.exam;
  var user = data.student;
  var questions = data.questions;

  var html = "";

  // exam
  html = "<dt>ID</dt><dd>" + exam.id + "</dd>";
  html += "<dt>Start</dt><dd>" + timestring(exam.start) + "</dd>";
  html += "<dt>End</dt><dd>" + timestring(exam.end) + "</dd>";
  html += "<dt>Errors</dt><dd>" + exam.errors + "</dd>";
  html += "<dt>Status</dt><dd>" + exam.status + "</dd>";
  $("#examinfotab #exam dd").remove();
  $("#examinfotab #exam dt").remove();
  $("#examinfotab #exam").append(html);

  // user
  html = "<dt>ID</dt><dd>" + user.id + "</dd>";
  html += "<dt>Name</dt><dd>" + user.name + " " + user.surname + "</dd>";
  $("#examinfotab #user dd").remove();
  $("#examinfotab #user dt").remove();
  $("#examinfotab #user").append(html);

  // questions
  $("#examinfotab table tbody tr").remove();
  var body = $("#examinfotab table tbody");
  var answer = false;
  var ok = "<span class='label label-success'><i class='icon-ok icon-white'></i></span>";
  var bad = "<span class='label label-important'><i class='icon-remove icon-white'></i></span>";
  for (var i = 0; i < questions.length; i++)
  {
    answer = questions[i].answer;
    correct = questions[i].is_correct;

    var html = "<tr>";
    html += "<td>" + (i + 1) + ".</td>";
    html += "<td>(" + questions[i].id +") "+ questions[i].text + "</td>";
    html += "<td>" + (answer ? "true":"false") + "</td>";

    html += "<td>" + (correct ? ok:bad) + "</td>";
    body.append(html);
  }
}
//----------------------------------------------------------------------------


function onTopicErrors()
{
  var user_id = $("#topicerrtab #id").val();
  var topic_id = $("#topicerrtab #topic").val();
  var lang = $("#topicerrtab #lang").val();
  var data = {}
  
  if (lang != "it")
    data.lang = lang;

  $.getJSON(url("/v1/student/"+user_id+"/topicerrors/"+topic_id), data, function(data) {
    if (data.status != 200)
      aux_showJSONError(data);
    else
      aux_fillTopicErrors(data);
  })
  .error(function(data) {
    aux_showError(data.responseText, data.status);
  });
}
//----------------------------------------------------------------------------

function aux_fillTopicErrors(data)
{
  var user = data.student;
  var questions = data.questions;

  var html = "";

  // user
  html = "<dt>ID</dt><dd>" + user.id + "</dd>";
  html += "<dt>Name</dt><dd>" + user.name + " " + user.surname + "</dd>";
  $("#topicerrtab #user dd").remove();
  $("#topicerrtab #user dt").remove();
  $("#topicerrtab #user").append(html);

  // questions
  $("#topicerrtab table tbody tr").remove();
  var body = $("#topicerrtab table tbody");
  var answer = false;
  for (var i = 0; i < questions.length; i++)
  {
    answer = questions[i].answer;
    correct = questions[i].is_correct;

    var html = "<tr>";
    html += "<td>" + (i + 1) + ".</td>";
    html += "<td>(" + questions[i].id +") "+ questions[i].text + "</td>";
    html += "<td>" + (answer ? "true":"false") + "</td>";
    body.append(html);
  }
}
//----------------------------------------------------------------------------


/*********************************************************
** Setup.
*********************************************************/

$(document).ready(function() {

  $(document).ajaxError(function() {
    aux_showError('Unexpected server response.')
  });

  doQuit();

  $("#bttQuit").click(doQuit);
  
  $(".form-signin .btn-primary").click(onAuth);

  $("#quiztab #bttQuizGet").click(onGetQuiz);
  $("#quiztab #bttQuizSend").click(onSendQuiz);
  $("#quiztab table thead input").change(onSelectAllQuestions);

  $("#examtab #bttExamGet").click(onGetExam);
  $("#examtab #bttExamSend").click(onSendExam);
  $("#examtab table thead input").change(onSelectAllQuestions);

  $("#reviewtab #bttReviewGet").click(onGetReview);
  $("#reviewtab #bttReviewSend").click(onSendReview);
  $("#reviewtab table thead input").change(onSelectAllQuestions);

  $("#studentstattab #bttStudentStatGet").click(onStudentStat);

  $("#examlisttab #bttGet").click(onStudentExams);

  $("#examinfotab #bttGet").click(onExamInfo);

  $("#topicerrtab #bttGet").click(onTopicErrors);
});
