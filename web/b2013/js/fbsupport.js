function fb_feed_post(message, link, title, description, pic_url, callback) {
    var fb_id = sessionStorage.getItem('quiz_fbid');
    if (!fb_id || 0 === fb_id.length)
        return;

    FB.getLoginStatus(function(response) {
        console.log(response.status);
        if (response.status === 'connected')
            fb_do_feed_post(message, link, title, description, pic_url,
                            callback);
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
