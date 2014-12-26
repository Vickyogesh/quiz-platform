(function() {
    SchoolStatModel = Backbone.Model.extend({
        defaults: {
            period: "current"
        },

        constructor: function() {
            this.stat = arguments[0].stat;
            delete arguments[0].stat;
            Backbone.Model.prototype.constructor.apply(this, arguments);
        },

        initialize: function() {

        },

        periodIndex: function() {
            var period = this.get("period");
            if (period == "current")
                return 0;
            else if (period == "week")
                return 1;
            else if (period == "week3")
                return 2;
            else
                return 3;
        },

        exams: function() {
            var index = this.periodIndex();
            return this.stat.exams[index];
        },

        guestVisits: function() {
            var index = this.periodIndex();
            var value =  this.stat.guest_visits[index];
            if (value == -1 || value === null)
                value = 0;
            return value;
        }
    });

    SchoolStatTopicsView = Backbone.View.extend({
        topic_tmpl: _.template($("#topic-tmpl").html() || ""),

        initialize: function() {
            this.listenTo(this.model, "change:period", this.render);
            this.renderTopics();
        },

        renderTopics: function() {
            var html = [];
            _.each(this.model.stat.topics, function(topic) {
                html.push(this.topic_tmpl({text: topic.text}));
            }.bind(this));
            this.$el.html(html);
            this.rows = this.$(".tablerow");
        },

        render: function() {
            var period = this.model.get("period");
             _.each(this.model.stat.topics, function(topic, index) {
                 var value = topic.errors[period];
                 var el = $(this.rows[index]).find(".graph");
                 el.empty();
                 draw_pie(el[0], value, {showEmpty: true});
             }.bind(this));
            return this;
        }
    });

    SchoolClientsRatingView = Backbone.View.extend({
        client_tmpl: _.template($("#client-tmpl").html() || ""),
        empty_client_tmpl: _.template($("#client-empty-tmpl").html() || ""),

        events: {
            "click a": "onClick"
        },

        initialize: function() {
            this.best_el = this.$("#best");
            this.worst_el = this.$("#worst");
            this.listenTo(this.model, "change:period", this.render);
            this.render();
        },

        do_render: function(el, type) {
            var period = this.model.get("period");
            var students = this.model.stat.students[period][type];
            var html = [];
            _.each(students, function(student) {
                html.push(this.client_tmpl({
                    fullname: student.surname + " " + student.name,
                    id: student.id
                }));
            }.bind(this));

            if (html.length == 0)
                el.html(this.empty_client_tmpl());
            else
                el.html(html);
        },

        render: function() {
            this.do_render(this.best_el, "best");
            this.do_render(this.worst_el, "worst");
        },

        onClick: function(event) {
            var name = $(event.currentTarget).find(".cell").html();
            this.trigger("click", $(event.currentTarget).attr("id"), name);
        }
    });

    SchoolStatView = Backbone.View.extend({
        events: {
            "click #navbar li": "onBttPeriod"
        },

        constructor: function() {
            var params = arguments[0];
            this.model = new SchoolStatModel({stat: params.stat});
            this.urls = params.urls;
            Backbone.View.prototype.constructor.apply(this, arguments);
        },

        initialize: function() {
            this.period_buttons = this.$("#navbar li");
            this.guest_visits_el = this.$("#visits");
            this.examgraph_el = this.$("#examgraph");

            this.clients = new SchoolClientsRatingView({
                el: this.$("#rating"),
                model: this.model
            });

            this.topics = new SchoolStatTopicsView({
                el: this.$("#topics"),
                model: this.model
            });

            this.listenTo(this.model, "change:period", this.onPeriodChanged);
            this.listenTo(this.clients, "click", this.onStudentClicked);

            this.render();
            this.topics.render();
        },

        onBttPeriod: function(event) {
            var a = $(event.currentTarget).find("a");
            a.blur();
            this.model.set("period", $(event.currentTarget).attr("data-period"));
        },

        onPeriodChanged: function() {
            var period = this.model.get("period");
            this.period_buttons.removeClass("active");
            this.$('#navbar li[data-period="' + period + '"]').addClass("active");
            this.render();
        },

        onStudentClicked: function(id, name) {
            var params = $.param({back: window.location.href, name: name});
            window.location = this.urls.stat + id + "?" + params;
        },

        render: function() {
            this.updateExamsAndGuestVisits();
            return this;
        },

        updateExamsAndGuestVisits: function() {
            var guest = this.model.guestVisits();
            var exams = this.model.exams();
            this.guest_visits_el.html(guest);

            this.examgraph_el.empty();
            draw_pie(this.examgraph_el[0], exams, {showEmpty: true});
        }
    });
})();
