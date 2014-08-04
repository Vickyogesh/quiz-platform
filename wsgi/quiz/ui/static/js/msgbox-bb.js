(function() {
    MessageBoxButton = Backbone.Model.extend({
        defaults: {
            type: "",
            text: "",
            icon: "",
            visible: true,
            callback: null
        },

        initialize: function() {
            this.on("change", function() {
              if (this.hasChanged("visible")) {
                this.trigger(this.get("visible") == true ? "show": "hide");
              }
            }, this);
        }
    });

    MessageBoxButtonView = Backbone.View.extend({
        default_tmpl: '<button type="button" class="btn <%= type %>" id="<%= id %>"><span class="glyphicon <%= icon %>"></span> <%= text %></button>',

        events: {
            "click": "onClick"
        },

        initialize: function() {
            var tmpl = $("#msg-box-button-tmpl").html();
            if (tmpl === undefined || tmpl.length == 0)
                tmpl = this.default_tmpl;
            this.template = _.template(tmpl);

            this.listenTo(this.model, "hide", this.onHide);
            this.listenTo(this.model, "show", this.onHide);
        },

        render: function() {
            var data = this.model.toJSON();
            this.$el.html(this.template(data));
            return this;
        },
        // handlers
        onShow: function() {
            this.$el.show();
        },
        onHide: function() {
            this.$el.hide();
        },
        onClick: function() {
            var callback = this.model.get("callback");
            if (callback !== undefined)
                callback.call(this.$el);
            this.trigger("click");
        }
    });

    MessageBoxButtonList = Backbone.Collection.extend({
       model: MessageBoxButton
    });

    MessageBoxModel = Backbone.Model.extend({
        initialize: function() {
            this.buttons = new MessageBoxButtonList;
        },

        addButton: function(params) {
            var button = new MessageBoxButton(params);
            this.buttons.add(button);
            return button;
        },

        button: function(id) {
            return this.get(id);
        },

        buttonAt: function(index) {
            return this.at(index);
        },

        hideButton: function(id) {
            this.button(id).set("visible", false);
        },

        showButton: function(id) {
            this.button(id).set("visible", true);
        }
    });

    MessageBox = Backbone.View.extend({
        default_tmpl: '<div><div><span class="glyphicon icon" id="icon"></span><p id="text"></p><div id="buttons"></div></div></div>',

        initialize: function() {
            this.icon_el = this.$("#icon");
            this.text_el = this.$("#text");

            var m = new MessageBoxModel;
            this.model = m;
            var mirror_functions = ["addButton", "hideButton", "showButton"];
            _.each(mirror_functions, function(name) {
                this[name] = m[name].bind(m);
            }, this);

            this.listenTo(this.model.buttons, "add", this.onAdd);
            this.listenTo(this.model, "change", this.render);

            this.$el.html(this.default_tmpl);
        },

        render: function () {
            this.icon_el.removeClass(this.model.previous("icon"));
            this.icon_el.addClass(this.model.get("icon"));
            this.text_el.html(this.model.get("text"));
            return this;
        },

        onAdd: function(button) {
            var btt_view = new MessageBoxButtonView({model: button});
            var lst = this.$("#buttons");
            var bel = btt_view.render().el;
            lst.append(bel);
        },

        show: function() {
            this.$el.show();
        }
    });
})();
