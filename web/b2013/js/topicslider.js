String.prototype.format = function() {
var args = arguments;
return this.replace(/{(\d+)}/g, function(match, number) { 
  return typeof args[number] != 'undefined'
    ? args[number]
    : match
  ;
});
};

function createPages(content_id, reduced) {
    var topics = [
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

    var chapters = [
        [1, 2, 3, 4], [5], [6], [7], [8], [9], [10, 11], [12], [13, 14], [15],
        [16, 17], [18], [19, 20, 21, 22, 23, 24, 25], [26], [27], [28],
        [29, 30, 31, 32, 33, 34, 35], [36, 37], [38, 39], [40, 41, 42, 43],
        [44, 45, 46], [47, 48], [49, 50], [51], [52, 53, 54]
    ];

    var areas = [
        [1],
        [2, 3, 4, 5, 6, 7, 8, 9, 10],
        [11, 12, 13, 14, 15, 16, 17],
        [18, 19],
        [20],
        [21, 22, 23],
        [24, 25]
    ];

    var quiz_url = "Quiz.html";

    if (reduced == true)
        quiz_url = "Quiz_reduced.html";

    var fmt_page = '<div id="page{0}" class="page area{0}" style="top:0px; left:0px; display:none"><table cellspacing="5px">';
    var fmt_chapter ='<tr><td width="30%" style="text-align:right">Capitolo {0}</td><td><a href="{2}?topic={3}">{1}</a></td></tr>';
    var fmt_topic ='<tr><td></td><td><a href="{1}?topic={2}">{0}</a></td></tr>';

    function new_page(area_id) {
        var area = areas[area_id - 1];

        var page = [fmt_page.format(area_id)];

        for (var i = 0; i < area.length; i++) {
            var chapter_id = area[i];
            var topic_list = chapters[chapter_id - 1];
            var topic_id = topic_list[0] - 1;
            var topic_title = topics[topic_id];
            page.push(fmt_chapter.format(chapter_id, topic_title, quiz_url, topic_id + 1));

            for (var j = 1; j < topic_list.length; j++) {
                topic_id = topic_list[j] - 1;
                topic_title = topics[topic_id];
                page.push(fmt_topic.format(topic_title, quiz_url, topic_id + 1));
            }

        }
        page.push('</table></div>');
        return page.join('');
    }

    var content = $(content_id + ' .slide');
    var items = [];
    for (var i = 0; i < 7; i++)
        items.push(new_page(i + 1));
    content.append(items.join(''));
}

function TopicSlider(element, reduced) {
    createPages(element + " #content", reduced);

    var obj = {
        current: null,
        current_index: 0,

        showPage: function(id) {
            if (this.current_index == id)
                return;

            var page = this.content.find("#page" + id);
            page.stop();
            page.css("margin-left", -this.content_width);
            page.height(this.content_height);
            page.width(this.content_width);
            page.show();

            var tbl = page.find("table");
            var delta = (this.content_height - tbl.height()) / 2;
            if (delta > 0)
                tbl.css("margin-top", delta + "px");
            else
                tbl.css("margin-top", "0px");

            if (this.current !== null) {
                var old_page = this.current;
                old_page.animate({
                    marginLeft: this.content_width
                });
                page.animate({
                    marginLeft: 0
                });
            }
            else
                page.css("margin-left", 0);

            this.current = page;
            this.current_index = id;
        },

        init: function(name) {
            var self = this;

            var elem = $(element);
            this.ul = elem.find(".row > div > ul");

            this.content = elem.find(".row > #content");
            this.content_height = this.content.height();
            this.content_width = this.content.width();
            this.content.find(".page").hide();
            this.showPage(1);

            this.ul.find('li').click(function(){
                var page_id = $(this).attr('data-id');
                self.showPage(page_id);
            });
        }
    }

    obj.init(element);
    return obj;
}
