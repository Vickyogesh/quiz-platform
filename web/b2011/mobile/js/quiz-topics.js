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

$("#page-quiz-topics").bind("pageinit", function() {
  $("#page-quiz-topics").bind('pagebeforeshow', function() {
    // var chapter = $("#page-quiz-chapters #chapters").attr('active-chapter');
    var chapter = sessionStorage.getItem("ch");
    var topic_ids = chapter_list[chapter - 1];
    var html = "";
    for (var i = 0; i < topic_ids.length; i++) {
      var id = topic_ids[i];
      html += '<li><a id="' + id + '">' + topic_list[id] + '</a></li>';
    }
    $("#page-quiz-topics #topics").html(html);
    $("#page-quiz-topics #topics").listview('refresh');
    $("#page-quiz-topics #topics li a").click(function(){
      sessionStorage.setItem("topic", $(this).attr("id"));
      $.mobile.changePage("#page-quiz", {transition: "slide"});
    });
  }); // pagebeforeshow

  $("#page-quiz-topics #bttLogout").click(function() {
    window.qsid = null;
    window.name = null;
    aux_busy(true);
    $.ajax("/v1/authorize/logout").always(function() {
        aux_busy(false);
        $.mobile.changePage("#page-login");
    });
  });
  $("#page-quiz-topics #bttBack").click(function() {
    $.mobile.changePage("#page-quiz-chapters",
                        {transition: "slide", reverse: true});
  });
});
