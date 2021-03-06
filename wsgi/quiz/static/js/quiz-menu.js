(function() {
    Topic = Backbone.Model.extend({});
    TopicList = Backbone.Collection.extend({model: Topic});
    Chapter = Backbone.Model.extend({
        initialize: function() {
            this.topics = new TopicList;
        }
    });
    ChapterList = Backbone.Collection.extend({model: Chapter});
    Area = Backbone.Model.extend({
        initialize: function() {
            this.chapters = new ChapterList;
        }
    });
    AreaList = Backbone.Collection.extend({model: Area});

    QuizMenu = Backbone.Model.extend({
        initialize: function() {
            this.areas = new AreaList;
            this.num = 0;
        },

        setData: function(areas, topics) {
            _.each(areas, function(area) {
                this.addArea(area, topics);
            }.bind(this));
        },

        addArea: function(area, topics) {
            var item = new Area({text: area.text, cls: area.cls});
            if (area.chapter_numbers !== undefined)
                this.num = 0;
            if (typeof area.chapters == "number") {
                for (var i = 0; i < area.chapters; ++i)
                    item.chapters.push(this.createChapter(topics, [],
                        area.chapter_numbers));
            }
            else {
                _.each(area.chapters, function (val) {
                    item.chapters.push(this.createChapter(topics, val,
                    area.chapter_numbers));
                }.bind(this));
            }
            this.areas.push(item);
        },

        createChapter: function(topics, id_list, chapter_numbers) {
            var chapter_num;
            if (chapter_numbers !== undefined)
                chapter_num = chapter_numbers[this.num++];
            else
                chapter_num = ++this.num;
            var chapter = new Chapter({"number": chapter_num});
            _.each(id_list, function(val) {
                chapter.topics.push({text: topics[val - 1], number: val});
            }.bind(this));
            return chapter;
        }
    });

    QuizAreaView = Backbone.View.extend({
        template: _.template($("#area-tmpl").html() || ""),
        tagName: "li",
        events: {"click": "onClick"},

        render: function() {
            var id = this.model.collection.indexOf(this.model) + 1;
            var cls = this.model.get("cls");
            if (cls === undefined)
                this.$el.attr("class", "area" + id);
            else
                this.$el.attr("class", cls);
            this.$el.attr("data-id", id);
            var html = this.template({text: this.model.get("text")});
            this.$el.html(html);
            return this;
        },

        onClick: function() {
            var id = this.model.collection.indexOf(this.model) + 1;
            this.trigger("click", id);
        }
    });

    QuizAreaPageView = Backbone.View.extend({
        template: _.template($("#page-tmpl").html() || ""),
        ch_template: _.template($("#chapter-tmpl").html() || ""),
        topic_template: _.template($("#topic-tmpl").html() || ""),

        constructor: function() {
            this.urls = arguments[0].urls;
            Backbone.View.prototype.constructor.apply(this, arguments);
        },

        quizUrl: function(topic_id) {

            var url = this.urls.quiz;
            url = url.replace('topic=0', 'topic='+topic_id);
            url = url.replace('quiz_type=0', 'quiz_type='+quiz_type);
            if (location.search.indexOf("ai=1") !== -1)
                url += "&ai=1";
            return url;
        },

        render: function() {
            var id = this.model.collection.indexOf(this.model) + 1;
            this.$el.attr("id", "page" + id);
            var cls = this.model.get("cls");
            if (cls === undefined)
                this.$el.attr("class", "page area" + id);
            else
                this.$el.attr("class", "page " + cls);
            this.$el.css("display", "none");

            var rows = [];
            this.model.chapters.each(function(chapter, index) {
                var topic = chapter.topics.at(0);
                var params = {chapter_id: chapter.get("number")};
                if (topic !== undefined) {
                    params.topic_text = topic.get("text");
                    params.topic_url = this.quizUrl(topic.get("number"));
                }
                else
                    params.topic_url = this.quizUrl(chapter.get("number"));

                rows.push(this.ch_template(params));
                chapter.topics.each(function(topic, index) {
                    if (index == 0)
                        return;
                    var params = {topic_url: this.quizUrl(topic.get("number")), topic_text: topic.get("text")};
                    rows.push(this.topic_template(params));
                }.bind(this));
            }.bind(this));

            this.$el.html(this.template({rows: rows.join("\n")}));
            return this;
        }
    });

    QuizMenuView = Backbone.View.extend({
        area_tmpl: _.template($("#area-tmpl").html() || ""),

        constructor: function() {
            var params = arguments[0];
            this.urls = params.urls;
            this.model = new QuizMenu;
            this.model.setData(params.areas, params.topics);
            Backbone.View.prototype.constructor.apply(this, arguments);
        },

        initialize: function() {
            this.areas_el = this.$(".areas ul").first();
            this.slides_el = this.$(".slides").first();
            this.current = null;
            this.current_index = 0;
            this.render();

            this.content_height = 0;
            this.content_width = this.slides_el.width();
            this.doResize();

            $(window).resize(this.doResize.bind(this));

            $("html").on("fullscreenChanged", this.updateGeom.bind(this));
            this.updateGeom();
            this.showPage(1);
        },

        updateGeom: function(ev, state) {
            var is_fullscreen = ev ? state : $("html").hasClass("is-fullscreen");
            if (is_fullscreen) {
                var html_h = $("html").height();
                var top = this.$el.offset().top;
                var fullscreen_height = html_h - top - 40;
                var item_height = fullscreen_height / this.model.areas.length;
                this.$el.find(".areas ul > li").css("height", item_height + "px");
            }
            else {
                this.$el.find(".areas ul > li").removeAttr("style");
            }
            this.content_width = this.slides_el.width();
            this.doResize();
        },

        render: function() {
            var areas_html = [];
            var pages_html = [];

            this.model.areas.each(function(area) {
                var item = new QuizAreaView({model: area});
                areas_html.push(item.render().$el);
                this.listenTo(item, "click", this.onClick);

                var pg = new QuizAreaPageView({model: area, urls: this.urls});
                pages_html.push(pg.render().$el);
            }.bind(this));

            this.areas_el.html(areas_html);
            this.slides_el.html(pages_html);
            return this;
        },

        doResize: function () {
            var h = this.areas_el.height();
            if (this.content_height != h) {
                this.content_height = h;
                this.slides_el.height(h);
                if (this.current)
                    this.current.height(h);
            }
        },

        onClick: function(id) {
            this.showPage(id);
        },

        showPage: function(id) {
            if (this.current_index == id)
                return;

            var page = this.slides_el.find("#page" + id);
            page.stop();
            page.css("margin-left", -this.content_width);
            page.height(this.content_height);
            page.show();

            if (this.current !== null) {
                var old_page = this.current;
                old_page.animate({marginLeft: this.content_width}, {complete: function() {
                    old_page.hide();
                }});
                page.animate({marginLeft: 0});
            }
            else
                page.css("margin-left", 0);

            this.current = page;
            this.current_index = id;
        }
    });

    $(".run-quiz").click(function () {
        var checked = $(".m_topic:checked");
        var topics = [];
        var url = ''; // url to run quiz. doesn't matter which topic if t_lst arg present

        checked.each(function (i, v) {
            url = $(v).attr('data-url');
            var t_id = Aux.getUrlParameterFromUrl(url, 'topic');
            topics.push(t_id);
        });
        if (topics.length > 0){
            window.location.href = url + "&t_lst=" + topics.join(",")
        }else {

        }
    })
})();
