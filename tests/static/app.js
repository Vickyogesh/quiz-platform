/*********************************************************
** AUX tools.
*********************************************************/

// Show error dialog
function aux_showError(msg)
{
  $("#msg .modal-body").html(msg)
  $("#msg").modal('show')
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


/*********************************************************
** Event handlers.
*********************************************************/

// Remove session cookie, hide features and show login dialog
function doQuit()
{
  $(document).cookie = 'QUIZSID=; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
  aux_showLogin();
}
//----------------------------------------------------------------------------

function onAuth()
{
  $.get("/v1/authorize").always(function(data) {
    if (data.status != 401)
    {
      aux_showError("Unexpected response. ");
      return;
    }

    var login = $(".form-signin #login").val();
    var passwd = $(".form-signin #pass").val();
    var info = data.getResponseHeader("WWW-Authenticate");
    var nonce = info.substring(info.indexOf('"')+1, info.length-1);

    var digest = CryptoJS.MD5(login + ':' + passwd);
    digest = CryptoJS.MD5(nonce + ':' + digest);

    var auth = 'QuizAuth nonce="' + nonce +
      '", appid="32bfe1c505d4a2a042bafd53993f10ece3ccddca", ' +
      ' username="' + login + '", digest="' + digest + '"';

    $.ajax({
      url: "/v1/authorize",
      type: "POST",
      beforeSend: function(xhr) {
        xhr.setRequestHeader("Authorization", auth);
      },
      error: function(data) {
        doQuit();
        aux_showError(data.responseText);
      },
      success: aux_showFeatures
    });

  });
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

function onGetQuiz()
{
  $("#quiztab table thead input").attr("checked", false);

  var topic = $("#quiztab #topic").val();
  var lang = $("#quiztab #lang").val();
  var uri = "/v1/quiz/" + topic;
  var data = {}
  if (lang != "it")
    data.lang = lang;

  $.getJSON(uri, data, function(data) {
    aux_fillTable($("#quiztab table"), data.questions);
  })
  .error(function(data) {
    aux_showError(data.responseText);
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

  var fd = new FormData();
  fd.append("id", id_list);
  fd.append("answer", answer_list);

  $.ajax({
    url: "/v1/quiz/" + topic,
    data: fd,
    processData: false,
    contentType: false,
    type: "POST",
    success: function(data) {
      aux_deselect($("#quiztab table"));
      aux_showInfo($("#quiztab"), "Done!");
   },
    error: function(data) {
      aux_showError(data.responseText);
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

  $.getJSON("/v1/exam", data, function(data) {
    aux_fillTable($("#examtab #examtable"), data);
  })
  .error(function(data) {
    aux_showError(data.responseText);
  });
}
//----------------------------------------------------------------------------

function onSendExam()
{
  aux_showError("Not implemented yet!");
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
  var body = $("#studentstattab tbody");

  $("#studentstattab .row #id").text(data.id);
  $("#studentstattab .row #name").text(data.name);

  var topics = data.topics;
  for (var t in topics)
  {
    var html = "<tr>";
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

  $.getJSON("/v1/student/"+user_id, data, function(data) {
    aux_fillUserStat(data);
  })
  .error(function(data) {
    aux_showError(data.responseText);
  });
}
//----------------------------------------------------------------------------


/*********************************************************
** Setup.
*********************************************************/

$(document).ready(function() {
  doQuit();

  $("#bttQuit").click(doQuit);
  
  $(".form-signin .btn-primary").click(onAuth);

  $("#quiztab #bttQuizGet").click(onGetQuiz);
  $("#quiztab #bttQuizSend").click(onSendQuiz);
  $("#quiztab table thead input").change(onSelectAllQuestions);

  $("#examtab #bttExamGet").click(onGetExam);
  $("#examtab #bttExamSend").click(onSendExam);
  $("#examtab table thead input").change(onSelectAllQuestions);

  $("#studentstattab #bttStudentStatGet").click(onStudentStat);
});
