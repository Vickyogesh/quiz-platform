(function() {
    Client = Backbone.Model.extend({
        defaults: {id: -1},

        fullName: function() {
            return this.get("name") + " " + this.get("surname");
        }
    });

    ClientList = Backbone.Collection.extend({
        model: Client,

        initialize: function(models, opts) {
            this.urls = opts.urls;
        },

        comparator: function(a, b) {
            return a.fullName().localeCompare(b.fullName());
        },

        removeAt: function(index) {
            var item = this.at(index);
            if (item === undefined)
                return;

            var id = item.get("id");
            var url = this.urls.remove + id + "?action=delete";

            Aux.postJson(url, function() {
                item.trigger("destroy");
            }.bind(this)).error(function(response) {
                this.trigger("error:remove", response);
            }.bind(this));
        },

        addClient: function(data) {
            data.passwd = md5(data.login + ':' + data.passwd);
            var url = this.urls.add;

            Aux.postJson(url, data, function(info) {
                delete data.passwd;
                data.id = info.id;
                this.add(data);
            }.bind(this)).error(function(response) {
                this.trigger("error:add", response);
            }.bind(this));
        },

        edit: function(index) {
            var id = this.at(index).get("id");
            var url = this.urls.change + "&uid=" + id;
            window.location = url;
        }
    });

    ClientView  = Backbone.View.extend({
        tagName: "a",
        className: "tablerow",

        events: {
            "click": "onClick",
            "click .edit": "onBttEdit",
            "click .remove": "onBttRemove"
        },

        // We use OR to allows packing this script to bundle.
        // If bundle is included to the file without #client-tmpl
        // then with OR it will not fail.
        template: _.template($("#client-tmpl").html() || ""),

        constructor: function() {
            var params = arguments[0];
            this.index = params.index;
            this.parent = params.parent;
            Backbone.View.prototype.constructor.apply(this, arguments);
        },

        initialize: function() {
            this.listenTo(this.model, "destroy", this.onRemove);
            this.listenTo(this.model, "change", this.render);
        },

        onClick: function() {
            this.parent.trigger("click", this.index);
        },

        onBttEdit: function(event) {
            event.stopPropagation();
            this.parent.trigger("edit", this.index);
        },

        onBttRemove: function(event) {
            event.stopPropagation();
            this.parent.trigger("remove", this.index);
        },

        onRemove: function() {
            this.$el.remove();
        },

        render: function() {
            var id = this.model.get("id");
            var name = this.model.fullName();
            var html = this.template({fullname: name});
            this.$el.html(html);
            this.$el.attr("id", id);
            this.$el.attr("href", "#");
            return this;
        }
    });

    ClientDialogAdd = BbDialog.extend({
         events: _.extend({}, BbDialog.prototype.events,{
            "input #name": "onChange",
            "input #surname": "onChange",
            "input #login": "onLogin"
        }),

        constructor: function() {
            this.labels = arguments[0].labels;
            BbDialog.prototype.constructor.apply(this, arguments);
        },

        initialize: function() {
            BbDialog.prototype.initialize.apply(this, arguments);
            this.name_el = this.$("#name");
            this.surname_el = this.$("#surname");
            this.login_el = this.$("#login");
            this.passwd_el = this.$("#passwd");
            this.can_set_login = true;

            this.setData({
                buttons: [
                    {type: "btn-primary",
                        text: this.labels.btt_add,
                        callback: this.onOk.bind(this)},
                    {text: this.labels.btt_cancel, is_cancel: true}
                ]
            });
        },

        onOk: function() {
            var data = {
                name: this.name_el.val(),
                surname: this.surname_el.val(),
                login: this.login_el.val(),
                passwd: this.passwd_el.val()
            };

            if (data.name.length == 0 || data.surname.length == 0
                || data.login.length == 0 || data.passwd.length == 0)
                return;

            this.trigger("done", data);
        },

        onChange: function() {
            if (this.can_set_login) {
                var name = this.name_el.val();
                var surname = this.surname_el.val();
                if (name.length != 0 && surname.length != 0)
                    name += ".";
                this.login_el.val((name + surname).toLowerCase());
            }
        },

        onLogin: function() {
            this.can_set_login = false;
        },

        clear: function() {
            this.name_el.val("");
            this.surname_el.val("");
            this.login_el.val("");
            this.passwd_el.val("");
            this.can_set_login = true;
        },

        show: function() {
            this.clear();
            BbDialog.prototype.show.apply(this, arguments);
        }
    });

    SchoolView = Backbone.View.extend({
        events: {
            "click #add-student": "onShowAddDialog"
        },

        constructor: function() {
            var params = arguments[0];
            this.model = new ClientList(params.clients, {urls:params.urls});
            this.labels = params.labels;
            this.urls = params.urls;
            Backbone.View.prototype.constructor.apply(this, arguments);
        },

        initialize: function() {
            this.clients_el = this.$("#clients");
            this.add_dlg = new ClientDialogAdd({el: this.$("#add-dlg"), labels: this.labels});
            this.dlg = new BbDialog({el: this.$("#dlg")});

            this.render();
            this.listenTo(this, "click", this.onClientClick);
            this.listenTo(this, "remove", this.onBttRemove);
            this.listenTo(this, "edit", this.onBttEdit);
            this.listenTo(this.add_dlg, "done", this.onAddDialogDone);
            this.listenTo(this.model, "add", this.onAdd);
            this.listenTo(this.model, "reset sort", this.render);
            this.listenTo(this.model, "error:add", this.onAddError);
            this.listenTo(this.model, "error:remove", this.onRemoveError);
        },

        render: function() {
            var html = [];
            this.model.each(function(client, index) {
                var row = new ClientView({model: client, index: index, parent: this});
                html.push(row.render().$el);
            }.bind(this));

            this.clients_el.empty();
            this.clients_el.html(html);
            return this;
        },

        onClientClick: function(index) {
            var id = this.model.at(index).get("id");
            window.location = this.urls.stat + id;
        },

        onBttRemove: function(index) {
            var item = this.model.at(index);

            function doit() {
                this.model.removeAt(index);
                this.dlg.hide();
            }

            this.dlg.show({
                title: this.labels.remove_title,
                text: sprintf(this.labels.remove_text, {name: item.fullName()}),
                buttons: [
                    {type: "btn-danger", text: this.labels.btt_remove,
                        callback: doit.bind(this)},
                    {text: this.labels.btt_cancel, is_cancel: true}
                ]
            });
        },

        onBttEdit: function(index) {
            this.model.edit(index);
        },

        onShowAddDialog: function() {
            this.add_dlg.show();
        },

        onAddDialogDone: function(data) {
            this.add_dlg.hide();
            this.model.addClient(data);
        },

        // Add view with support of sorting
        onAdd: function(model) {
            var index = this.model.indexOf(model);
            var row = new ClientView({model: model, index: index, parent: this});
            var el = row.render().$el;
            var current_rows = this.clients_el.find(row.tagName);

            if (current_rows.length == 0 || index == this.model.length - 1)
                this.clients_el.append(el);
            else if (index == 0)
                el.prependTo(this.clients_el);
            else
                el.insertAfter(current_rows[index - 1]);
        },

        onAddError: function(response) {
            this.dlg.show({
                title: this.labels.error_title,
                text: this.labels.add_error_text,
                buttons: [
                    {text: this.labels.btt_close, is_cancel: true}
                ]
            });
        },

        onRemoveError: function(response) {
            this.dlg.show({
                title: this.labels.error_title,
                text: this.labels.remove_error_text,
                buttons: [
                    {text: this.labels.btt_close, is_cancel: true}
                ]
            });
        }
    });
})();
