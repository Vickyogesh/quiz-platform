function fb_feed_post(message, link, title, description, pic_url, callback) {
    var fb_id = sessionStorage.getItem('quiz_fbid');
    if (!fb_id || 0 === fb_id.length) {
        callback(null);
        return;
    }

    FB.getLoginStatus(function(response) {
        console.log(response.status);
        if (response.status === 'connected')
            fb_do_feed_post(message, link, title, description, pic_url,
                            callback);
        else
            callback(null);
    });
}

function fb_do_feed_post(message, link, title, description, pic_url, callback) {
    var opts = {
        message: message,
        name : title,
        link : link,
        description : description,
        picture : pic_url
    };

    FB.api('/me/feed', 'post', opts, callback);
}

function fb_set_user_pic(sel) {
    var fb_id = sessionStorage.getItem('quiz_fbid');
    console.log("fb_id", fb_id);
    if (!fb_id || 0 === fb_id.length)
        return;
    
    var pic = sessionStorage.getItem("fbuser_pic");
    if (pic !== null) {
        _do_fb_set_user_pic(sel);
        return;
    }

    if (window.FB === undefined) {
        console.log("FB init");
        $.getScript('//connect.facebook.net/en_UK/all.js', function() {
            FB.init({
                appId: '306969962800273',
                version: "v2.0",
                status: true
            });
            FB.getLoginStatus(function(response) {
                console.log(response.status);
                if (response.status === 'connected')
                    _fb_set_user_pic_apicall(sel);
            });
        });
    }
    else
        _fb_set_user_pic_apicall(sel);
}

function _fb_set_user_pic_apicall(sel) {
    FB.api(
        "/me/picture",
        "get",
        {
            "redirect": false,
            "height": "30",
            "type": "normal",
            "width": "30"
        },
        function (response) {
            if (response && !response.error) {
                sessionStorage.setItem("fbuser_pic", response.data.url);
                _do_fb_set_user_pic(sel);
            }
            else
                console.log("pic ask", response.error);
        }
    );                
}

function _do_fb_set_user_pic(sel) {
    var pic = sessionStorage.getItem("fbuser_pic");
    $(sel).attr("src", pic);
    $(sel).show();
}
