(function() {
    function createPages(content_id) {
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
        var fmt_page = '<div id="page%1$s" class="page area%1$s" style="display:none"><div class="page-wrapper"><div class="page-content"><table>';
        var fmt_chapter ='<tr><td width="30%%" style="text-align:right">Capitolo %(ch)s</td><td><a href="%(url)s%(tid)s">%(title)s</a></td></tr>';
        var fmt_topic ='<tr><td></td><td><a href="%(url)s%(tid)s">%(title)s</a></td></tr>';

        function new_page(area_id) {
            var area = areas[area_id - 1];

            var page = [sprintf(fmt_page, area_id)];

            for (var i = 0; i < area.length; i++) {
                var chapter_id = area[i];
                var topic_list = chapters[chapter_id - 1];
                var topic_id = topic_list[0] - 1;
                var topic_title = topics[topic_id];
                var opts = {ch: area[i], url: window.g.quiz_url, tid: topic_id + 1, title: topic_title};
                page.push(sprintf(fmt_chapter, opts));

                for (var j = 1; j < topic_list.length; j++) {
                    topic_id = topic_list[j] - 1;
                    topic_title = topics[topic_id];
                    opts = {url: window.g.quiz_url, tid: topic_id + 1, title: topic_title};
                    page.push(sprintf(fmt_topic, opts));
                }

            }
            page.push('</table></div></div></div>');
            return page.join('');
        }

        var slides = $(content_id);
        var items = [];
        for (var i = 0; i < 7; i++)
            items.push(new_page(i + 1));
        slides.append(items.join(''));
    }

    TopicSlider = function(element) {
        createPages(element + " .slides");

        var obj = {
            current: null,
            current_index: 0,

            showPage: function(id) {
                if (this.current_index == id)
                    return;

                var page = this.slides.find("#page" + id);
                page.stop();
                page.css("margin-left", -this.content_width);
                page.height(this.content_height);
                page.show();

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

            do_resize: function () {
                var h = this.areas.height();
                if (this.content_height != h) {
                    this.content_height = h;
                    this.slides.height(h);
                    if (this.current)
                        this.current.height(h);
                }
            },

            init: function(name) {
                var self = this;

                var elem = $(element);
                this.areas = elem.find(".areas");
                this.ul = this.areas.find("ul");

                this.slides = elem.find(".slides");
                this.content_height = 0; //this.areas.height();
                this.content_width = this.slides.width();
                this.do_resize();
                this.slides.find(".page").hide();
                this.showPage(1);

                this.ul.find('li').click(function(){
                    var page_id = $(this).attr('data-id');
                    self.showPage(page_id);
                });

                $(window).resize(function() {
                    self.do_resize();
                });
            }
        }

        obj.init(element);
        return obj;
    }
}).call(this);
