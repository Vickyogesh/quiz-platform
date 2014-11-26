$("#page-quiz-list").bind("pageinit", function() {
    var topic_list = [
        "Definizioni stradali e di traffico",
        "Definizioni e classificazione dei veicoli",
        "Doveri del conducente nell'uso della strada - convivenza civile",
        "Riguardo verso gli utenti deboli della strada",
        "Segnali di pericolo",
        "Segnali di divieto",
        "Segnali di obbligo",
        "Segnali di precedenza",
        "Segnaletica orizzontale - Segni sugli ostacoli",
        "Segnalazioni semaforiche",
        "Segnalazioni degli agenti del traffico",
        "Segnali di indicazione",
        "Segnali complementari",
        "Segnali temporanei e di cantiere",
        "Pannelli integrativi dei segnali",
        "Pericolo e intralcio alla circolazione - Comportamenti ai passaggi a livello",
        "Limiti di velocità",
        "Distanza di sicurezza",
        "Norme sulla circolazione dei veicoli",
        "Posizione dei veicoli sulla carreggiata",
        "Cambio di direzione o di corsia (svolta)",
        "Rischi legati alla manovra - campo visivo del conducente",
        "Comportamento agli incroci",
        "Norme sulla precedenza",
        "Comportamento in presenza di cortei - Obblighi verso i veicoli di Polizia e di emergenza",
        "Esempi di precedenza (ordine di precedenza agli incroci)",
        "Norme sul sorpasso",
        "Fermata, sosta, arresto e partenza",
        "Ingombro della carreggiata",
        "Segnalazione di veicolo fermo",
        "Norme sulla circolazione in autostrada e strade extraurbane principali",
        "Trasporto di persone",
        "Carico dei veicoli - Pannelli sui veicoli",
        "Traino dei veicoli e dei veicoli in avaria - Traino dei rimorchi",
        "Rischi nella guida",
        "Uso delle luci - Uso dei dispositivi acustici",
        "Spie e simboli",
        "Equipaggiamento - Cinture e sistemi di ritenuta per bambini",
        "Casco protettivo - Abbigliamento di sicurezza",
        "Patenti di guida",
        "Documenti di circolazione del veicolo",
        "Obbligo verso funzionari ed agenti - Sistema sanzionatorio",
        "Patente a punti",
        "Comportamenti per prevenire incidenti stradali",
        "Peculiarità della guida di motocicli",
        "Comportamento in caso di incidente stradale",
        "Guida in relazione alle condizioni fisiche e psichiche - Alcool, droga e farmaci",
        "Primo soccorso",
        "Responsabilità civile, penale, amministrativa",
        "Assicurazione R.C.A. - Altre forme assicurative legate al veicolo",
        "Limitazione dei consumi - Rispetto dell'ambiente - Inquinamento",
        "Elementi costitutivi del veicolo importanti per la sicurezza - Manutenzione ed uso",
        "Stabilità e tenuta di strada del veicolo",
        "Comportamenti e cautele di guida"
    ];

    var chapter_list = [
        [1, 2, 3, 4], [5], [6], [7], [8], [9], [10, 11], [12], [13, 14], [15],
        [16, 17], [18], [19, 20, 21, 22, 23, 24, 25], [26], [27], [28],
        [29, 30, 31, 32, 33, 34, 35], [36, 37], [38, 39], [40, 41, 42, 43],
        [44, 45, 46], [47, 48], [49, 50], [51], [52, 53, 54]
    ];

    var chapter_area = [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3,
                        3, 3, 3, 3, 3, 4, 4, 5, 6, 6, 6, 7, 7];

    $("#page-quiz-list #bttLogout").click(function() {
        window.name = null;
        aux_busy(true);
        $.ajax(url("/v1/authorize/logout")).always(function() {
            aux_deleteServicesCookies();
            aux_busy(false);
            $.mobile.changePage("#page-login");
        });
    });

    $("#page-quiz-list #bttBack").click(function() {
        $.mobile.changePage("#page-student",
                            {transition: "slide", reverse: true});
    });

    var html = [];
    var chapter_fmt = "<li data-role='list-divider' class='area{0}'>Capitolo {1}</li>";
    var topic_fmt = "<li><a id='{0}'>{1}</a></li>";
    for (var i = 0; i < chapter_list.length; ++i) {
        html.push(chapter_fmt.format(chapter_area[i], i + 1));
        var topics = chapter_list[i];
        for (var j = 0; j < topics.length; ++j) {
            var id = topics[j];
            html.push(topic_fmt.format(id, topic_list[id - 1]));
        }
        html.push("</li>");
    }
    $("#page-quiz-list #topics").html(html.join(''));
    $("#page-quiz-list #topics").listview('refresh');
    $("#page-quiz-list #topics li a").click(function(){
      sessionStorage.setItem("topic", $(this).attr("id"));
      $.mobile.changePage("#page-quiz", {transition: "slide"});
    });
    
});
