(function () {
    MessageBoxButton = Backbone.Model.extend({
        defaults: {type: "", text: "", icon: ""}
    });

    MessageBoxButtonList = Backbone.Collection.extend({
       model: MessageBoxButton
    });

    MessageBoxModel = Backbone.Model.extend({
        initialize: function() {
            this.buttons = new MessageBoxButtonList;
        }
    });

    MessageBoxButtonView = Backbone.View.extend({
        default_tmpl: '<span class="glyphicon <%= icon %>"></span> <%= text %>',
        events: {
            "click": "onClick"
        },
        tagName: "button",
        className: "btn",

        initialize: function() {
            var tmpl = $("#msgbox-button-tmpl").html();
            if (tmpl === undefined || tmpl.length == 0)
                tmpl = this.default_tmpl;
            this.template = _.template(tmpl);
        },

        render: function() {
            var data = this.model.toJSON();
            this.$el.attr("type", "button");
            this.$el.addClass(this.model.get("type"));
            this.$el.html(this.template(data));
            return this;
        },

        onClick: function() {
            var callback = this.model.get("callback");
            if (callback !== undefined)
                callback.call(this.$el);
        }
    });

    MessageBox = Backbone.View.extend({
        default_tmpl: '<div><div><span class="glyphicon icon" id="icon"></span><p id="text"></p><div id="buttons"></div></div></div>',

        initialize: function() {
            this.$el.html(this.default_tmpl);
            this.icon_el = this.$("#icon");
            this.text_el = this.$("#text");
            this.buttons_el = this.$("#buttons");

            this.model = new MessageBoxModel;
            this.listenTo(this.model, "change", this.setInfo);
            this.listenTo(this.model.buttons, "reset change", this.setButtons);
        },

        setInfo: function() {
            this.icon_el.removeClass(this.model.previous("icon"));
            this.icon_el.addClass(this.model.get("icon"));
            this.text_el.html(this.model.get("text"));
        },

        setButtons: function() {
            var self = this;
            this.buttons_el.empty();
            this.model.buttons.each(function(item) {
                var btt = new MessageBoxButtonView({model: item});
                self.buttons_el.append(btt.render().el);
            });
        },

        show: function(data) {
            if (data === undefined)
                this.$el.show();
            else {
                var buttons = data.buttons;
                delete data.buttons;
                this.model.set(data);
                this.model.buttons.reset(buttons);
                this.$el.show();
            }
            this.trigger("show");
        },

        hide: function() {
            this.$el.hide();
            this.trigger("hide");
        }
    });
})();
