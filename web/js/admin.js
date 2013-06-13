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
  doLogout();
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
      login: login,
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
        var name = data.user.name;
        if (data.user.surname)
          name += ' ' + data.user.surname;
        $("#features #uname").text(data.user.type + ': ' + name)
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

function aux_errSpan(err) {
    if (err == -1)
      return " N/A ";
    else
      return " " + err + "% ";
    // if (err == -1)
    //   return "<div class='span1'><span class='label label-important'>N/A</span></div>";
    // else if (err >= 20 )
    //   return "<div class='span1'><span class='badge badge-important'>" + err + "%</span></div>";
    // else if (err > 0)
    //   return "<div class='span1'><span class='badge badge-warning'>" + err + "%</span></div>";
    // else
    //   return "<div class='span1'><span class='badge badge-success'>" + err + "%</span></div>";
}

function aux_fillUserStat(data)
{
  var html = "";
  var body = $("#studentstattab tbody");
  body.find("tr").remove();

  $("#studentstattab .row #id").text(data.student.id);
  $("#studentstattab .row #name").text(data.student.name + ' ' + data.student.surname);

  var exams = data.exams;
  html = aux_errSpan(exams.current) + aux_errSpan(exams.week) + aux_errSpan(exams.week3)
  $("#studentstattab .row #exams").html(html);

  var topics = data.topics;
  for (var t in topics)
  {
    var topic = topics[t]
    html = "<tr>";
    html += "<td>" + (+t + 1) + ".</td>";
    html += "<td>" + topic.text + "</td>";

    var err = topic.errors;
    var a = err.current;
    var b = err.week;
    var c = err.week3;
    html += "<td>" + aux_errSpan(a) + aux_errSpan(b) + aux_errSpan(c) + "</td>";

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
    if (data.status != 200)
      aux_showJSONError(data);
    else
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

function onAddSchool()
{
  $("#admintab #admin_add").modal('show');
  $("#admintab #admin_add input").val('');
}
//----------------------------------------------------------------------------

function onDoAddSchool()
{
  var name = $("#admintab #admin_add #name").val();
  var login = $("#admintab #admin_add #login").val();
  var passwd = $("#admintab #admin_add #passwd").val();

  var data = {
    name: name,
    login: login,
    passwd: hex_md5(login + ':' + passwd)
  };

  $("#admintab #admin_add").modal('hide');

  aux_postJSON(url("/v1/admin/newschool"), data, function (data) {
    if (data.status != 200)
      aux_showJSONError(data);
    else
      aux_showInfo($("#admintab"), "Done!");
  })
  .error(function(data) {
    aux_showError(data.responseText, data.status);
  });
}
//----------------------------------------------------------------------------

function onDelSchool(p, school_id)
{
  $.ajax({
    url: url("/v1/admin/school/" + school_id),
    type: "DELETE",
    success: function(data) {
    if (data.status != 200)
      aux_showJSONError(data);
    else
      $(p).toggleClass("btn-danger");
    }
  })
  .error(function(data) {
    aux_showError(data.responseText, data.status);
  });
}
//----------------------------------------------------------------------------

function aux_fillSchools(data)
{
  var html = "";
  var lst = data.schools;
  var body = $("#admintab table tbody");
  $("#admintab table tbody tr").remove();

  for (var i = 0; i < lst.length; i++)
  {
    var html = "<tr>";
    html += "<td>" + lst[i].id + ".</td>";
    html += "<td>" + lst[i].name + "</td>";
    html += "<td>" + lst[i].login + "</td>";
    html += "<td><a class='btn btn-danger' onclick='onDelSchool(this, " + lst[i].id + ")'>"
      + "Delete</a></td>";
    body.append(html);
  }
}
//----------------------------------------------------------------------------

function onSchoolList()
{
  $.getJSON(url("/v1/admin/schools"), function(data) {
    if (data.status != 200)
      aux_showJSONError(data);
    else
      aux_fillSchools(data);
  })
  .error(function(data) {
    aux_showError(data.responseText, data.status);
  });
}
//----------------------------------------------------------------------------


function onAddStudent()
{
  $("#schooltab #school_add").modal('show');
  $("#schooltab #school_add input").val('');
}
//----------------------------------------------------------------------------

function onDoAddStudent()
{
  var sid = $("#schooltab #school_id").val();
  var name = $("#schooltab #school_add #name").val();
  var surname = $("#schooltab #school_add #surname").val();
  var login = $("#schooltab #school_add #login").val();
  var passwd = $("#schooltab #school_add #passwd").val();

  var data = {
    name: name,
    surname: surname,
    login: login,
    passwd: hex_md5(login + ':' + passwd)
  };

  $("#schooltab #school_add").modal('hide');

  aux_postJSON(url("/v1/school/" + sid + "/newstudent"), data, function (data) {
    if (data.status != 200)
      aux_showJSONError(data);
    else
      aux_showInfo($("#schooltab"), "Done!");
  });

}
//----------------------------------------------------------------------------

function onDelStudent(p, school_id, student_id)
{
  $.ajax({
    url: url("/v1/school/" + school_id + "/student/" + student_id),
    type: "DELETE",
    success: function(data) {
    if (data.status != 200)
      aux_showJSONError(data);
    else
      $(p).toggleClass("btn-danger");
    }
  })
  .error(function(data) {
    aux_showError(data.responseText, data.status);
  });
}
//----------------------------------------------------------------------------

function aux_fillStudents(data, school_id)
{
  var html = "";
  var lst = data.students;
  var body = $("#schooltab table tbody");
  $("#schooltab table tbody tr").remove();

  for (var i = 0; i < lst.length; i++)
  {
    var html = "<tr>";
    html += "<td>" + lst[i].id + ".</td>";
    html += "<td>" + lst[i].name + " " + lst[i].surname + "</td>";
    html += "<td>" + lst[i].login + "</td>";
    html += "<td><a class='btn btn-danger' "
      + "onclick='onDelStudent(this, \"" + school_id + "\"," + lst[i].id + ")'>"
      + "Delete</a></td>";
    body.append(html);
  }
}
//----------------------------------------------------------------------------

function onStudentlList()
{
  $("#schooltab #stat").addClass("hide");
  $("#schooltab #students").removeClass("hide");

  var sid = $("#schooltab #school_id").val();

  $.getJSON(url("/v1/school/" + sid + "/students"), function(data) {
    if (data.status != 200)
      aux_showJSONError(data);
    else
      aux_fillStudents(data, sid);
  })
  .error(function(data) {
    aux_showError(data.responseText, data.status);
  });
}
//----------------------------------------------------------------------------

function aux_getRatingDiv(data)
{
  function toLi(info) {
    if (info == undefined)
      return"<li>N/A</li>";
    else
      return "<li>" + info.name + ' ' + info.surname + "</li>";
  }

  if (data == undefined)
    return "<ul><li>N/A</li><li>N/A</li><li>N/A</li></ul>";

  var html = "<ul>";
  html += toLi(data[0]);
  html += toLi(data[1]);
  html += toLi(data[2]);
  html += "</ul>";
  return html;
}
//----------------------------------------------------------------------------


function aux_fillSchoolStat(data)
{
  var html = "";
  var body = $("#schooltab #stat #info");

  var students = data.students;

  html += "<div class='row'>";
  html += "<div class='span2'><b>Current</b></div>";
  html += "<div class='span2'><b>best</b>";
  html += aux_getRatingDiv(students.current.best);
  html += "</div>";
  html += "<div class='span2'><b>worst</b>";
  html += aux_getRatingDiv(students.current.worst);
  html += "</div>";
  html += "</div>";

  html += "<div class='row'>";
  html += "<div class='span2'><b>Week</b></div>";
  html += "<div class='span2'><b>best</b>";
  html += aux_getRatingDiv(students.week.best);
  html += "</div>";
  html += "<div class='span2'><b>worst</b>";
  html += aux_getRatingDiv(students.week.worst);
  html += "</div>";
  html += "</div>";

  html += "<div class='row'>";
  html += "<div class='span2'><b>Week3</b></div>";
  html += "<div class='span2'><b>best</b>";
  html += aux_getRatingDiv(students.week3.best);
  html += "</div>";
  html += "<div class='span2'><b>worst</b>";
  html += aux_getRatingDiv(students.week3.worst);
  html += "</div>";
  html += "</div>";

  body.html(html);

  $("#schooltab #stat .row #guest_visits").text(data.guest_visits);
  $("#schooltab #stat .row #exams").text(data.exams);

  body = $("#schooltab #stat #topics tbody");
  body.find("tr").remove();
  var topics = data.topics;
  for (var t in topics)
  {
    var topic = topics[t]
    html = "<tr>";
    html += "<td>" + (+t + 1) + ".</td>";
    html += "<td>" + topic.text + "</td>";

    var err = topic.errors;
    var a = err.current;
    var b = err.week;
    var c = err.week3;
    html += "<td>" + aux_errSpan(a) + aux_errSpan(b) + aux_errSpan(c) + "</td>";

    body.append(html);
  }
}
//----------------------------------------------------------------------------

function onSchoolStat()
{
  var sid = $("#schooltab #school_id").val();

  $("#schooltab #stat").removeClass("hide");
  $("#schooltab #students").addClass("hide");

  $.getJSON(url("/v1/school/" + sid), function(data) {
    if (data.status != 200)
      aux_showJSONError(data);
    else
       aux_fillSchoolStat(data);
  })
  .error(function(data) {
    aux_showError(data.responseText, data.status);
  });
}
//----------------------------------------------------------------------------

function onContinue()
{
  aux_showFeatures();
}
//----------------------------------------------------------------------------


/*********************************************************
** Setup.
*********************************************************/

$(document).ready(function() {

  $(document).ajaxError(function() {
    aux_showError('Unexpected server response.')
  });

  $("#bttQuit").click(doQuit);
  
  $(".form-signin .btn-primary").click(onAuth);
  $(".form-signin #continue").click(onContinue);
  $(".form-signin #quit").click(doQuit);

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

  $("#admintab #bttAdd").click(onAddSchool);
  $("#admintab #admin_add .btn-success").click(onDoAddSchool);
  $("#admintab #bttGet").click(onSchoolList);

  $("#schooltab #bttAdd").click(onAddStudent);
  $("#schooltab #school_add .btn-success").click(onDoAddStudent);
  $("#schooltab #bttGet").click(onStudentlList);
  $("#schooltab #bttGetStat").click(onSchoolStat);
});
