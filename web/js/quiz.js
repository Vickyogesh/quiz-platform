var topic_list = [
    "Definizioni stradali e di traffico",
    "Definizioni e classificazione dei veicoli",
    "Doveri del conducente ed uso responsabile della strada",
    "Riguardo verso gli utenti deboli della strada",
    "Segnali di pericolo",
    "Segnali di divieto",
    "Segnali di obbligo",
    "Segnali di precedenza",
    "Segnaletica orizzontale",
    "Segnalazioni semaforiche",
    "Segnalazioni degli agenti del traffico",
    "Segnali di indicazione",
    "Segnali complementari",
    "Segnali temporanei e di cantiere",
    "Pannelli integrativi dei segnali",
    "Pericolo e intralcio alla circolazione - Limiti di velocità",
    "Distanza di sicurezza",
    "Norme sulla circolazione dei veicoli",
    "Posizione dei veicoli sulla carreggiata",
    "Cambio di direzione o di corsia (svolta)",
    "Comportamento agli incroci",
    "Norme sulla precedenza",
    "Comportamento in presenza di cortei - Obblighi verso i veicoli di polizia",
    "Esempi di precedenza (ordine di precedenza agli incroci)",
    "Norme sul sorpasso",
    "Fermata, sosta, arresto e partenza",
    "Ingombro della carreggiata",
    "Segnalazione di veicolo fermo",
    "Norme sulla circolazione in autostrada e strade extraurbane principali",
    "Trasporto di persone",
    "Carico dei veicoli - Pannelli sui veicoli",
    "Traino dei veicoli e dei veicoli in avaria",
    "Rischi nella guida",
    "Uso delle luci - Uso dei dispositivi acustici - Spie e simboli",
    "Equipaggiamento - Cinture e sistemi di ritenuta per bambini - Casco",
    "Documenti di circolazione del veicolo",
    "Comportamenti per prevenire incidenti - Comportamento in caso di incidente",
    "Guida in relazione alle condizioni psicofisiche - Alcool, droga e farmaci",
    "Primo soccorso",
    "Responsabilità civile, penale, amministrativa",
    "Assicurazione R.C.A. - Altre forme assicurative legate al veicolo",
    "Limitazione dei consumi - Rispetto dell'ambiente - Inquinamento",
    "Stabilità e tenuta di strada del veicolo",
    "Elementi del veicolo importanti per la sicurezza - Manutenzione ed uso",
    "Comportamenti e cautele di guida"
];      
var chapter_list = [
    [1, 2, 3, 4], [5], [6], [7], [8], [9], [10, 11], [12], [13, 14], [15], [16],
    [17], [18, 19, 20, 21, 22, 23], [24], [25], [26],
    [27, 28, 29, 30, 31, 32, 33], [34], [35], [36], [37], [38, 39], [40, 41],
    [42], [43, 44, 45]
];

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

function saveState() {
    for (i = 0; i < quizData.length; i++) {
        if (current_answers[i] != null) {
            if (parseInt(quizData[i].answer) != current_answers[i]) {
                total_errors++;
            }
        }
    }

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
        //console.log("do_get", force);
        WaitMsg.show();
        var p = uri;
        if (force)
            p += "?force=true";
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
        $("#quizarea #topic h1").html(topic_list[data.topic-1]);

        function hasQuestion(id) {
            return idMap[id];
        }

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
    
    if (curIndex == quizData.length - 3) {
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
        
        $("#imagearea > div").hide();
        $("#imagearea img").attr("src", "");

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
            
            if (i == curIndex && quizData[i].image !== ""
                && quizData[i].image !== undefined) {
                var image = "/img/" + quizData[i].image + ".jpg";
                $("#imagearea img").attr("src", image);
                $("#imagearea span").html("fig. " + quizData[i].image);
                $("#imagearea > div").show();

                // preload next image
                if (i + 1 < quizData.length && quizData[i + 1].image != "") {
                    image = "/img/" + quizData[i + 1].image + ".jpg";
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
                if (current_answers[i] == 1) {
                    id = "#quiz0" + (j+1) + " .topt";               
                    $(id).attr('src', 'img/true_selected.png');
                    id = "#quiz0" + (j+1) + " .fopt";               
                    $(id).attr('src', 'img/false.png');         
                }
                else if (current_answers[i] == 0) {
                    id = "#quiz0" + (j+1) + " .topt";               
                    $(id).attr('src', 'img/true.png');
                    id = "#quiz0" + (j+1) + " .fopt";               
                    $(id).attr('src', 'img/false_selected.png');
                }
                
                // checking answer is correct
                id = "#quiz0" + (j+1) + " .answer";
                if (bAnswerOn == true) {
                    if (parseInt(quizData[i].answer) == current_answers[i]) {
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
}

$(document).ready(function() {
    var i, j, htmlVal;
    
    $("#topicgroup #chapterarea").empty();
    for (i = 0; i < chapter_list.length; i++) {
        htmlVal = '<div id="chapter' + (i+1)
                + '" class="slider chap" style="font-size:15px; background-color:#707070; cursor:pointer;">';
        htmlVal += '<p style="padding-left:10px; float:left">';
        htmlVal += '<a>Capitolo ' + (i+1) + '</a>';
        htmlVal += '<div id="expandsign" style="float:right; width:15px; height:15px; margin:7px"></div>';
        htmlVal += '</p></div>';
        htmlVal += '<div id="topiclist' + (i+1) + '" class="slider" style="display:none">';
        for (j = 0; j < chapter_list[i].length; j++) {
            htmlVal += '<p id="' + chapter_list[i][j] + '" class="result"><a href="#">'
            + chapter_list[i][j] + '. ' + topic_list[chapter_list[i][j]-1] + '</a></p>';
        }           
        htmlVal += '</div>';
        
        $("#topicgroup #chapterarea").append(htmlVal);
    }   

    window.qsid = sessionStorage.getItem('quizqsid');       
    
    $("#quizarea").hide();
    
    $(".result").click(function(){          
        topicIndex = $(this).attr("id");
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
                alert('Done! Number of errors: ' + total_errors);
                setQuizEnv();
            }
        });
    });     
    
    $('#backbut, #backbut1').click(function(){
        window.location = "student.html";
    });
    
    
    $('#quizlistarea').mousewheel(function(event, delta, deltaX, deltaY) {
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
