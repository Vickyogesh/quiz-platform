var groups = [
    "Parte comune",
    "Parte specialistica Trasporto di merci",
    "Parte specialistica Trasporto di persone"
];
var group_topics = [
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    [11, 12, 13], [14, 15, 16]
];
var group_index = 0;

var bAnswerOn = false;
var bTerminated = false;
var topicIndex;

var curIndex;
var current_ids = [];
var current_answers = [];

var idMap = {}
var quizData = [];
var total_ids = [];
var total_answers = [];
var total_errors = 0;
var can_ask_more = true;

function saveState() {
    current_ids = [];
    current_answers = [];
}

function push_answer(index, ans) {
    var qid = quizData[index].id;
    // console.log('push_answer for '+ qid, index, ans);

    total_ids.push(qid);
    total_answers.push(ans);
    current_ids.push(qid);
    current_answers.push(ans);
}

function sendAnswers(callback) {
    if (current_ids.length == 0)
        return

    // console.log('send answers ln='+ current_ids.length + ': ' + current_ids)
    var data = {
        questions: current_ids,
        answers: current_answers
    };
    saveState();

    if (callback === undefined)
        callback = function(data) {
            if (data.status != 200) {
                WaitMsg.hide();
                aux_showJSONError(data);
                setQuizEnv();
            }
        }
    aux_postJSON(url("/v1/quiz/" + topicIndex), data, callback);
}

// TODO: really?
function alreadyAnswered(nIndex) {
    if (nIndex >= 0 && nIndex < total_ids.length) {     
        for (i = 0; i < total_ids.length; i++) {
            if (quizData[nIndex].id == total_ids[i])
                break;
        }
        if (i == total_ids.length)
            return false;
        else 
            return true;
    }
    else {
        return false;
    }
}

function fillupQuiz(force) {
    //console.log("fillupQuiz", force);
    var lang = "it";
    var uri = url("/v1/quiz/" + topicIndex);
    var data = {};
    
    if (lang != "it")
        data.lang = lang;

    function do_get(d, force, on_ok) {
        var exclude = []
        for (var i = curIndex; i < quizData.length; i++)
            exclude.push(quizData[i].id);

        //console.log("do_get", force);
        WaitMsg.show();
        var p = uri;

        if (exclude.length != 0)
            p += "?exclude=" + exclude.toString();
        if (force) {
            if (exclude.length != 0)
                p += '&';
            else
                p += '?';
            p += "force=true";
        }
        $.getJSON(p, d, function(info) {
            if (info.status != 200) {
                WaitMsg.hide();
                aux_showJSONError(info);
            }
            else
                on_ok(info);
        });
    }

    function do_show(data) {
        // console.log("do_show", data.questions.length);
        // var tmp = []
        // for (var i = 0; i < data.questions.length; i++)
        //     tmp.push(data.questions[i].id);
        // console.log(tmp.toString());

        WaitMsg.hide();
        $("#topicgroup").hide();
        $("#quizarea").show();
        $("#quizarea #topic h1").html(groups[group_index]);

        function hasQuestion(id) {
            return idMap[id];
        }

        can_ask_more = data.questions.length == 40;
        for (var i = 0; i < data.questions.length; i++) {
            var q = data.questions[i];
            if (!hasQuestion(q.id)) {
                quizData.push(q);
                idMap[q.id] = true;
            }
        }
        // console.log("total", quizData.length);
        // tmp = [];
        // for (var i = 0; i < quizData.length; i++)
        //     tmp.push(quizData[i].id);
        // console.log(tmp.toString());
        //console.log(data.questions.length);
        setQuizEnv();
    }

    sendAnswers();
    do_get(data, false, function (info) {
        if (info.questions.length == 0) {
            if (!force) {
                WaitMsg.hide();
                return;
            }
            WaitMsg.hide();
            var b = confirm(
                "Hai risposto a tutte le domande di questo argomento!" +
                "\nContinuare comunque?");
            if (b)
                do_get(data, true, do_show);
        }
        else
            do_show(info);
    });
}

function showNext() {
    if (curIndex < quizData.length) {
        curIndex++;
        setQuizEnv();
    }
    
    if (can_ask_more && curIndex == quizData.length - 3) {
        fillupQuiz();
    }
}

var img_preload = new Image();
function setQuizEnv() { 
    var quizhtml1, quizhtml2;
    var i, j = 0;
    
    quizhtml1 = '<div class="text" style="background-color:#4c739f">';
    quizhtml1 += '</div>';
    quizhtml1 += '<div class="answer" style="background-color:#4c739f;">';
    quizhtml1 += '<img class="topt" src="img/true.png"/>';
    quizhtml1 += '<img class="fopt" src="img/false.png" />';
    quizhtml1 += '</div>';          
    
    quizhtml2 = '<div class="text" style="background-color:#869fbb;">';
    quizhtml2 += '</div>';
    quizhtml2 += '<div class="answer" style="background-color:#869fbb;">';
    quizhtml2 += '<img class="topt" src="img/true.png"/>';
    quizhtml2 += '<img class="fopt" src="img/false.png" />';
    quizhtml2 += '</div>';          
    
    if (bTerminated == false) {
        // removing     
        if (curIndex == 0) {
            $("#quiz01").empty();
            $("#quiz02").empty();
        }
        else if (curIndex == 1) {
            $("#quiz01").empty();       
            $("#quiz02").empty();
            $("#quiz02").append(quizhtml2);
        }
        else if (curIndex == 2) {
            $("#quiz01").empty();       
            $("#quiz01").append(quizhtml1);
        }           
        
        //console.log('window [' +(curIndex - 2)+', '+(curIndex +3)+'] max='
                    // +quizData.length +', current='+curIndex);

        for (i = curIndex - 2; i < curIndex + 3; i++, j++) {
            var id;
                        
            if (i < 0) {
                continue;               
            }
            else if (i >= quizData.length) {
                id = "#quiz0" + (j+1);
                $(id).empty();
                continue;
            }
                            
            if (j == 2)
                id = "#quiz0" + (j+1) + " .maintext p";
            else 
                id = "#quiz0" + (j+1) + " .text";
            
            var text = quizData[i].id.toString() + " | " + quizData[i].text;
            $(id).html(text);
            
            id = "#quiz0" + (j+1) + " .answer";
            $(id).removeClass('trueAnswer');
            $(id).removeClass('falseAnswer');
            
            id = "#quiz0" + (j+1) + " .topt";
            $(id).attr('src', 'img/true.png');              

            id = "#quiz0" + (j+1) + " .fopt";
            $(id).attr('src', 'img/false.png');                 
            
            if (alreadyAnswered(i) == true) {
                if (total_answers[i] == 1) {
                    id = "#quiz0" + (j+1) + " .topt";               
                    $(id).attr('src', 'img/true_selected.png');
                    id = "#quiz0" + (j+1) + " .fopt";               
                    $(id).attr('src', 'img/false.png');         
                }
                else if (total_answers[i] == 0) {
                    id = "#quiz0" + (j+1) + " .topt";               
                    $(id).attr('src', 'img/true.png');
                    id = "#quiz0" + (j+1) + " .fopt";               
                    $(id).attr('src', 'img/false_selected.png');
                }
                
                // checking answer is correct
                id = "#quiz0" + (j+1) + " .answer";
                if (bAnswerOn == true) {
                    if (parseInt(quizData[i].answer) == total_answers[i]) {
                        $(id).addClass('trueAnswer');
                    }
                    else {
                        $(id).addClass('falseAnswer');
                    }
                }
            }
        }
        
        var ansHeight = $("#quiz03 .maintext").height();
        var ansTop = (ansHeight - $("#quiz03 .topt").height()) / 2;
        $("#quiz03 .answer").height(ansHeight);
        $("#quiz03 .topt").css('margin-top', ansTop + 'px');
        $("#quiz03 .fopt").css('margin-top', ansTop + 'px');
    }
    else {
        // removing
        $("#scrollbararea").hide();
        $('#quizlistarea').empty();

        var style = "";
        if (is_reduced) {
            $('#quizlistarea').width(720);
            $('#quizlistarea').height(192);
            style = '" style="width:700px; height:31px; margin-top:5px">';
        }
        else {
            $('#quizlistarea').width(930);
            $('#quizlistarea').height(250);
            style = '" style="width:920px; height:40px; margin-top:10px">';
        }
        
        var html;
        quizhtml2 = '<div class="maintext" style="background-color:#869fbb;">';
        quizhtml2 += '<p></p></div>';
        quizhtml2 += '<div class="answer" style="background-color:#869fbb;">';
        quizhtml2 += '<img class="topt" src="img/true.png"/>';
        quizhtml2 += '<img class="fopt" src="img/false.png" />';
        quizhtml2 += '</div>';          
        
        for (i = 0; i < quizData.length; i++) {
            html = '<div id="quiz0' + (i+1) + style;
            html += quizhtml2;
            html += '</div>';
            
            $('#quizlistarea').append(html);
            $('#quizlistarea').css('overflow-y', 'scroll');
            $('#quizlistarea').css('overflow-x', 'hidden');
                            
            id = "#quiz0" + (i+1) + " .maintext p";
            var text = quizData[i].id.toString() + " | " + quizData[i].text;
            $(id).html(text);
            
            if (total_answers[i] == 1) {
                id = "#quiz0" + (i+1) + " .topt";               
                $(id).attr('src', 'img/true_selected.png');
                id = "#quiz0" + (i+1) + " .fopt";               
                $(id).attr('src', 'img/false.png');         
            }
            else if (total_answers[i] == 0) {
                id = "#quiz0" + (i+1) + " .topt";               
                $(id).attr('src', 'img/true.png');
                id = "#quiz0" + (i+1) + " .fopt";               
                $(id).attr('src', 'img/false_selected.png');
            }
            
            // checking answer is correct
            id = "#quiz0" + (i+1) + " .answer";

            if (total_answers[i] != null) {
                $(id).removeClass('trueAnswer');
                $(id).removeClass('falseAnswer');
                
                if (parseInt(quizData[i].answer) == total_answers[i]) {
                    $(id).addClass('trueAnswer');
                }
                else {
                    total_errors++;
                    $(id).addClass('falseAnswer');
                }
            }

            id = "#quiz0" + (i+1);
            var ansHeight = $(id + " .maintext").height();
            var ansTop = (ansHeight - $(id + " .topt").height()) / 2;
            $(id + " .answer").height(ansHeight);
            $(id + " .answer").css("margin-top", $(id + " .maintext").css("margin-top"));
            $(id + " .topt").css('margin-top', ansTop + 'px');
            $(id + " .fopt").css('margin-top', ansTop + 'px');

        }
    }
    
    // set height of the scroll bar
    var nHeight = $("#quizlistarea").height() + 20;
    $("#scrollbararea").css('height', nHeight + 'px');
}

$(document).ready(function() {
    var i, j, htmlVal;
    
    $("#topicgroup #chapterarea").empty();

    for (i = 0; i < groups.length; i++) {
        htmlVal = '<div id="chapter' + (i+1)
                + '" class="slider chap" style="font-size:15px; background-color:#707070; cursor:pointer;">';
        htmlVal += '<p style="padding-left:10px; float:left">';
        htmlVal += '<a>' + groups[i] + '</a>';
        htmlVal += '<div id="expandsign" style="float:right; width:15px; height:15px; margin:7px"></div>';
        htmlVal += '</p></div>';
        htmlVal += '<div id="topiclist' + (i+1) + '" class="slider" style="display:none">';
        for (j = 0; j < group_topics[i].length; j++) {
            htmlVal += '<p id="' + group_topics[i][j] +
            '" class="result" gid="' + i + '""><a href="#">Capitolo ' + group_topics[i][j] +
            '</a></p>';
        }           
        htmlVal += '</div>';
        
        $("#topicgroup #chapterarea").append(htmlVal);
    }   

    window.qsid = sessionStorage.getItem('quizqsid');       
    
    // Image preload
    var img1 = new Image();
    var img2 = new Image();
    img1.src = "img/true_selected.png";
    img2.src = "img/false_selected.png";

    $("#quizarea").hide();
    
    $(".result").click(function(){          
        topicIndex = $(this).attr("id");
        group_index = $(this).attr("gid");
        curIndex = 0;
        fillupQuiz(true);           
    });
    
    $("#tbutton").click(function(){
        if (alreadyAnswered(curIndex) == false) {
            push_answer(curIndex, 1);
            showNext();
        }
    });     
    $("#fbutton").click(function(){
        if (alreadyAnswered(curIndex) == false) {
            push_answer(curIndex, 0);
            showNext();
        }
    });
    
    $('#iswitch').iphoneSwitch("off", 
        function() {
            bAnswerOn = true;
            setQuizEnv();
        },
        function() {
            bAnswerOn = false;
            setQuizEnv();
        });
    
    $('#endbut').click(function(){
        if (current_ids.length == 0)
            return;
        WaitMsg.show();
        bTerminated = true;

        sendAnswers(function(data) {
            if (data.status != 200) {
                WaitMsg.hide();
                aux_showJSONError(data);
                setQuizEnv();
            }
            else
            {
                WaitMsg.hide();
                total_errors = 0;
                setQuizEnv();
                alert('Done! Number of errors: ' + total_errors);
            }
        });
    });     
    
    $('#backbut, #backbut1').click(function(){
        window.location = "student.html";
    });
    
    
    $('#quizlistarea').mousewheel(function(event, delta, deltaX, deltaY) {
        if (bTerminated) {
            return;
        }
        if (deltaY > 0) {
            if (alreadyAnswered(curIndex - 1) == true) {
                curIndex--;
                setQuizEnv();
            }
        }               
        else if (deltaY < 0) {
            if (alreadyAnswered(curIndex) == true) {
                curIndex++;
                setQuizEnv();
            }
        }
        
        if (bTerminated == false) {
            return false;
        }
    });
    
    $('#scrollup').click(function(){
        if (alreadyAnswered(curIndex - 1) == true) {
            curIndex--;
            setQuizEnv();
        }
    });     
    $('#scrollup').mousedown(function(){
        $(this).css('background-image','url("img/scrollUpSel.png")');
    });
    $('#scrollup').mouseup(function(){
        $(this).css('background-image','url("img/scrollUp.png")');
    });     
    
    $('#scrolldown').click(function(){
        if (alreadyAnswered(curIndex) == true) {
            curIndex++;
            setQuizEnv();
        }
    });
    $('#scrolldown').mousedown(function(){
        $(this).css('background-image','url("img/scrollDownSel.png")');
    });
    $('#scrolldown').mouseup(function(){
        $(this).css('background-image','url("img/scrollDown.png")');
    });     
            
    for (i = 1; i <= 25; i++) {
        var esignid = '#chapter' + i + ' #expandsign';
        $(esignid).addClass('collapse');
    }
    
    $('.slider.chap').click(function(){
        var checkElement = $(this).next();
        var esignid = '#' + $(this).attr('id') + ' #expandsign';
        
        if(checkElement.is(':visible')) {               
            checkElement.slideUp('normal');
            $(esignid).removeClass('expand');
            $(esignid).addClass('collapse');
        }
        if(!checkElement.is(':visible')) {
            checkElement.slideDown('normal');
            $(esignid).removeClass('collapse');
            $(esignid).addClass('expand');
        }
    });
});
