(function() {
    var default_html =
        '<div class="message-layer" id="%s"><div><div>' +
        '<span class="glyphicon icon" id="icon"></span>' +
        '<p id="text"></p><div id="buttons"></div></div></div></div>';

    MessageLayer = function(parent_id, id) {
        this.html = sprintf(default_html, id);
        $(parent_id).append(this.html);

        this.el = $(parent_id + " #" + id).first();
        this.icon_el = this.el.find("#icon");
        this.icon_el_class = '';
        this.text_el = this.el.find("#text");
        this.buttons_el = this.el.find("#buttons");
        this.buttons_count = 0;
        this.button_fmt = "<button type=\"button\" class=\"btn %s\" id=\"%s\"><span class=\"glyphicon %s\"></span> %s</button>";
        this.on_hide = null;
        this.on_show = null;

        this.set_icon = function(icon_class) {
            if (this.icon_el_class != icon_class) {
                this.icon_el.removeClass(this.icon_el_class);
                this.icon_el_class = icon_class;
                this.icon_el.addClass(this.icon_el_class);
            }
        };

        this.set_text = function(text) {
            this.text_el.html(text);
        };

        this.show = function(state) {
            if (state == true || state === undefined) {
                this.el.show();
                if (this.on_show !== null)
                    this.on_show();
            }
            else {
                this.el.hide();
                if (this.on_hide !== null)
                    this.on_hide();
            }
        };

        this.clear_buttons = function() {
            this.buttons_el.empty();
            this.buttons_count = 0;
        };

        this.add_button = function(btn_class, icon_class, id, text, callback) {
            var html = sprintf(this.button_fmt, btn_class, id, icon_class, text);
            this.buttons_el.append(html);

            if (callback !== undefined)
                this.buttons_el.find("#" + id).click(callback);
        };

        this.on = function(button_id, callback) {
            var btt = this.buttons_el.find("#" + button_id);
            btt.unbind("click");
            btt.click(callback);
        };
    };
})();
