(function() {
    function saveFbId(userId, callback) {
        var data = {userId: userId};
        var url = window.g.link_fb_url;
        Aux.postJson(url, data, function(data) {
            Aux.showInfo(window.g.labels.fb_connect_ok, callback);
        }).error(function(response) {
            console.log(response);
            Aux.showInfo(window.g.labels.fb_connect_fail);
        });
    }

    this.FbAux = {
        linkFbAccount: function(callback) {
            FB.login(function(response) {
                if (response.status === 'connected')
                    saveFbId(response.authResponse.userID, callback);
            }, {scope: 'public_profile'});
        },

        post: function(data) {
            var opts = {
                message: data.message,
                name : data.title,
                link : data.link,
                description : data.description,
                picture : data.pic_url
            };
            FB.api('/me/feed', 'post', opts);
        }
    };
}).call(this);
