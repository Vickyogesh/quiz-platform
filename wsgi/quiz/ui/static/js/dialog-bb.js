// Backbone wrapper for the bootstrap modal.
(function() {
    BbDialogButton = Backbone.Model.extend({
        defaults: {type: "", text: "", icon: "", is_cancel: false}
    });

    BbDialogButtonList = Backbone.Collection.extend({
       model: BbDialogButton
    });

    BbDialogModel = Backbone.Model.extend({
        defaults: {
            title: "",
            text: ""
        },
        initialize: function() {
            this.buttons = new BbDialogButtonList;
        }
    });

    BbDialogButtonView = Backbone.View.extend({
        default_tmpl: '<span class="glyphicon <%= icon %>"></span> <%= text %>',
        events: {
            "click": "onClick"
        },
        tagName: "button",
        className: "btn",

        initialize: function() {
            var tmpl = $("#bbdialog-button-tmpl").html();
            if (tmpl === undefined || tmpl.length == 0)
                tmpl = this.default_tmpl;
            this.template = _.template(tmpl);
        },

        render: function() {
            var data = this.model.toJSON();
            this.$el.attr("type", "button");
            this.$el.addClass(data.type || "btn-default");
            if (data.is_cancel == true)
                this.$el.attr("data-dismiss", "modal");
            if (data.icon !== undefined)
                this.$el.html(this.template(data));
            else
                this.$el.html(data.text);
            return this;
        },

        onClick: function() {
            var callback = this.model.get("callback");
            if (callback !== undefined)
                callback();
        }
    });

    // NOTE: you have to provide 'el'.
    BbDialog = Backbone.View.extend({
        initialize: function() {
            this.title_el = this.$("#dlg-label");
            this.body_el = this.$(".modal-body");
            this.footer_el = this.$(".modal-footer");
            this.$el.modal({show: false});

            this.model = new BbDialogModel;
            this.listenTo(this.model, "change:title", this.setTitle);
            this.listenTo(this.model, "change:text", this.setText);
            this.listenTo(this.model.buttons, "reset change", this.setButtons);
        },

        setTitle: function() {
            this.title_el.html(this.model.get("title"));
        },

        setText: function() {
            this.body_el.html(this.model.get("text"));
        },

        setButtons: function() {
            this.footer_el.empty();
            this.model.buttons.each(function(item) {
                var btt = new BbDialogButtonView({model: item});
                this.footer_el.append(btt.render().el);
            }.bind(this));
        },

        setData: function(data) {
            var buttons = data.buttons;
            delete data.buttons;
            this.model.set(data);
            this.model.buttons.reset(buttons);
        },

        show: function(data) {
            if (data !== undefined)
                this.setData(data);
            this.$el.modal("show");
            this.trigger("show");
        },

        hide: function() {
            this.$el.modal("hide");
            this.trigger("hide");
        }
    });
})();
