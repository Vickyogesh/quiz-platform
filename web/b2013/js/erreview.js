var curIndex;
var currentIds = [];
var currentAnswers = [];
var quizMap = {};
var quizIds = [];
var canAskMore = true;
var bAnswerOn = false;
var bTerminated = false;

function saveState() {
    currentIds = [];
    currentAnswers = [];
}

function push_answer(index, ans) {
    var qid = quizIds[index];
    var q = quizMap[qid];
    q.user_answer = ans;
    currentIds.push(qid);
    currentAnswers.push(ans);
}

function sendAnswers(callback) {
    if (currentIds.length == 0)
        return;

    // console.log('send answers ln='+ currentIds.length + ': ' + currentIds)
    var data = {
        questions: currentIds,
        answers: currentAnswers
    };
    saveState();

    if (callback === undefined)
        callback = function(data) {
            if (data.status != 200) {
                WaitMsg.hide();
                var user = sessionStorage.getItem('quizutype');
                if (user == 'guest' && data.status == 403)
                    showGuestAccessError();
                else
                    aux_showJSONError(data);
                setQuizEnv();
            }
        }
    aux_postJSON(url("/v1/errorreview"), data, null).always(callback);
}

function alreadyAnswered(nIndex) {
    var qid = quizIds[nIndex];

    if (qid === undefined || quizMap[qid] === undefined)
        return false;
    return quizMap[qid].user_answer !== undefined;
}

function fillupReview() {
    WaitMsg.show();
    sendAnswers();

    var lang = "it";
    var uri = url("/v1/errorreview");
    var data = {};
    
    if (lang != "it")
        data.lang = lang;
    
    var exclude = []
    var start = Math.max(0, quizIds.length - 40);
    for (var i = start; i < quizIds.length; i++)
        exclude.push(quizIds[i]);
    if (exclude.length != 0)
        uri += "?exclude=" + exclude.toString();

    $.getJSON(uri, data).always(function(data) {
        if (data.status != 200) {
            var user = sessionStorage.getItem('quizutype');
            if (user == 'guest' && data.status == 403) {
                WaitMsg.hide();
                showGuestAccessError();
                window.location = "student.html";
            }
            else {
                WaitMsg.hide();
                aux_showJSONError(data);
            }
        }
        else {
            WaitMsg.hide();
            
            $("#reviewarea").show();                

            canAskMore = data.questions.length == 40;
            for (var i = 0; i < data.questions.length; i++) {
                var q = data.questions[i];

                quizIds.push(q.id);
                if (quizMap[q.id] === undefined)
                    quizMap[q.id] = q;
                else
                    delete quizMap[q.id].user_answer;
            }
            // console.log(data.questions.length);
            setQuizEnv();
        }
    });
}

function showNext() {
    if (curIndex < quizIds.length) {
        curIndex++;
        setQuizEnv();
    }
    
    if (canAskMore && curIndex == quizIds.length - 3) {
        fillupReview();
    }
}

var img_preload = new Image();
function setQuizEnv() { 
    
    var quizhtml1, quizhtml2;
    var i, j = 0;
    
    quizhtml1 = '<div class="text" style="background-color:#818183">';
    quizhtml1 += '</div>';
    quizhtml1 += '<div class="answer" style="background-color:#818183;">';
    quizhtml1 += '<img class="topt" src="img/true.png"/>';
    quizhtml1 += '<img class="fopt" src="img/false.png" />';
    quizhtml1 += '</div>';          
    
    quizhtml2 = '<div class="text" style="background-color:#a9a9ab;">';
    quizhtml2 += '</div>';
    quizhtml2 += '<div class="answer" style="background-color:#a9a9ab;">';
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

        $("#imagearea > div img").hide();
        $("#imagearea > div span").hide();
        $("#imagearea img").attr("src", "");

        for (i = curIndex - 2; i < curIndex + 3; i++, j++) {
            var id;
                        
            if (i < 0) {
                continue;               
            }
            else if (i >= quizIds.length) {
                id = "#quiz0" + (j+1);
                $(id).empty();
                continue;
            }

            if (j == 2)
                id = "#quiz0" + (j+1) + " .maintext p";
            else 
                id = "#quiz0" + (j+1) + " .text";
            
            var q = quizMap[quizIds[i]];
            var text = q.id.toString() + " | " + q.text;
            $(id).html(text);
            
            if (i == curIndex && q.image !== ""
                && q.image !== undefined) {
                var image = "/img/" + q.image + ".jpg";
                $("#imagearea img").attr("src", image);
                $("#imagearea span").html("fig. " + q.image);
                $("#imagearea > div img").show();
                $("#imagearea > div span").show();

                // preload next image
                if (i + 1 < quizIds.length && quizMap[quizIds[i + 1]].image != "") {
                    image = "/img/" + quizMap[quizIds[i + 1]].image + ".jpg";
                    img_preload.src = image;
                }
            }

            id = "#quiz0" + (j+1) + " .answer";
            $(id).removeClass('trueAnswer');
            $(id).removeClass('falseAnswer');
            
            id = "#quiz0" + (j+1) + " .topt";
            $(id).attr('src', 'img/true.png');              

            id = "#quiz0" + (j+1) + " .fopt";
            $(id).attr('src', 'img/false.png');     
            
            if (alreadyAnswered(i) == true) {
                if (q.user_answer == 1) {
                    id = "#quiz0" + (j+1) + " .topt";               
                    $(id).attr('src', 'img/true_selected.png');
                    id = "#quiz0" + (j+1) + " .fopt";               
                    $(id).attr('src', 'img/false.png');         
                }
                else if (q.user_answer == 0) {
                    id = "#quiz0" + (j+1) + " .topt";               
                    $(id).attr('src', 'img/true.png');
                    id = "#quiz0" + (j+1) + " .fopt";               
                    $(id).attr('src', 'img/false_selected.png');
                }
                
                // checking answer is correct
                id = "#quiz0" + (j+1) + " .answer";
                if (bAnswerOn == true) {
                    if (parseInt(q.answer) == q.user_answer) {
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
            $('#quizlistarea').width(560);
            $('#quizlistarea').height(192);
            style = '" style="width:578px; height:31px; margin-top:5px">';
        }
        else {
            $('#quizlistarea').width(730);
            $('#quizlistarea').height(250);
            style = '" style="width:750px; height:40px; margin-top:10px">';
        }

        var html;
        quizhtml2 = '<div class="maintext" style="background-color:#869fbb;">';
        quizhtml2 += '<p></p></div>';
        quizhtml2 += '<div class="answer" style="background-color:#869fbb;">';
        quizhtml2 += '<img class="topt" src="img/true.png"/>';
        quizhtml2 += '<img class="fopt" src="img/false.png" />';
        quizhtml2 += '</div>';          
        
        var already_displayed = {};
        for (i = 0; i < quizIds.length; i++) {
            var qid = quizIds[i];

            // If we already show this question - skip.
            if (already_displayed[qid] !== undefined)
                continue;

            already_displayed[qid] = true;
            var q = quizMap[qid];

            // Hide unanswered questions
            if (q.user_answer === undefined)
                continue;

            html = '<div id="quiz0' + (i+1) + style;
            html += quizhtml2;
            html += '</div>';
            
            $('#quizlistarea').append(html);
            $('#quizlistarea').css('overflow-y', 'scroll');
            $('#quizlistarea').css('overflow-x', 'hidden');
                            
            id = "#quiz0" + (i+1) + " .maintext p";

            var text = q.id.toString() + " | " + q.text;

            $(id).html(text);
            
            if (q.user_answer == 1) {
                id = "#quiz0" + (i+1) + " .topt";               
                $(id).attr('src', 'img/true_selected.png');
                id = "#quiz0" + (i+1) + " .fopt";               
                $(id).attr('src', 'img/false.png');         
            }
            else if (q.user_answer == 0) {
                id = "#quiz0" + (i+1) + " .topt";               
                $(id).attr('src', 'img/true.png');
                id = "#quiz0" + (i+1) + " .fopt";               
                $(id).attr('src', 'img/false_selected.png');
            }

            // checking answer is correct
            id = "#quiz0" + (i+1) + " .answer";

            if (q.user_answer !== undefined) {
                $(id).removeClass('trueAnswer');
                $(id).removeClass('falseAnswer');
                
                if (parseInt(q.answer) == q.user_answer) {
                    $(id).addClass('trueAnswer');
                }
                else {
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
    var nHeight = $("#quizlistarea").height();
    $("#scrollbararea").css('height', nHeight + 'px');

    if (quizIds.length == 0)
    {
        alert("Non ci sono errori");
        window.location = "student.html";
    }
}

$(document).ready(function() {
    var i, htmlVal;

    window.qsid = sessionStorage.getItem('quizqsid');

    // Image preload
    var img1 = new Image();
    var img2 = new Image();
    img1.src = "img/true_selected.png";
    img2.src = "img/false_selected.png";

    $("#reviewarea").hide();
    $("#reviewarea #topic h1").html("Ripasso Errori");
    
    curIndex = 0;
    fillupReview();
    
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
    
    $('#endbut').click(function() {
        // function getNumErrors() {
        //     var num = 0;
        //     for (var id in quizMap) {
        //         var q = quizMap[id];
        //         if (q.answers != q.user_answer)
        //             num++;
        //     }
        //     return num;
        // }

        if (currentIds.length == 0)
            return;

        WaitMsg.show();
        bTerminated = true;

        sendAnswers(function(data) {
            if (data.status != 200) {
                WaitMsg.hide();
                var user = sessionStorage.getItem('quizutype');
                if (user == 'guest' && data.status == 403)
                    showGuestAccessError();
                else
                    aux_showJSONError(data);
                setQuizEnv();
            }
            else
            {
                WaitMsg.hide();
                //alert('Done! Number of errors: ' + getNumErrors());
                setQuizEnv();
            }
        });
    });     
    
    $('#backbut').click(function(){
        window.location = "student.html";
    });
    
    $('#reviewarea').mousewheel(function(event, delta, deltaX, deltaY) {
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
});
