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
    var areas = [
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        [11, 12, 13],
        [14, 15, 16]
    ];

    var quiz_url = "Quiz.html";

    if (reduced == true)
        quiz_url = "Quiz_reduced.html";

    var classes = ["generale", "merci", "persone"];
    var fmt_page = '<div id="page{0}" class="page {1}" style="top:0px; left:0px; display:none"><div class="topics">';
    var fmt = '<div><a href="{2}?topic={1}">Capitolo {0}</a></div>';

    var fmt_chapter ='<tr><td width="30%" style="text-align:right"></td><td><a href="{2}?topic={1}">{0}</a></td></tr>';
    var fmt_topic ='<tr><td></td><td><a href="{2}?topic={1}">Capitolo {0}</a></td></tr>';

    function new_page(area_id) {
        var area = areas[area_id - 1];

        var page = [fmt_page.format(area_id, classes[area_id - 1])];

        for (var i = 0; i < area.length; i++) {
            var topic_id = area[i];
            page.push(fmt.format(topic_id, topic_id, quiz_url));
        }
        page.push('</div></div></div>');
        return page.join('');
    }

    var content = $(content_id + ' .slide');
    var items = [];
    for (var i = 0; i < 3; i++)
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

            var tbl = page.find(".topics");
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
