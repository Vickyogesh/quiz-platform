(function() {
    // Fullscreen docs:
    // http://johndyer.name/native-fullscreen-javascript-api-plus-jquery-plugin/
    // http://davidwalsh.name/fullscreen
    // http://html5.by/blog/fullscreen-javascript-api/
    var iframe_html;

    function requestFullScreen(el) {
        if (el.requestFullScreen)
            el.requestFullScreen();
        else if (el.mozRequestFullScreen)
            el.mozRequestFullScreen();
        else if (el.webkitRequestFullScreen)
            el.webkitRequestFullScreen();
        else if (el.msRequestFullscreen)
            el.msRequestFullscreen();
    }

    function cancelFullScreen() {
        if (document.cancelFullScreen)
            document.cancelFullScreen();
        else if (document.mozCancelFullScreen)
            document.mozCancelFullScreen();
        else if (document.webkitCancelFullScreen)
            document.webkitCancelFullScreen();
        else if (document.msExitFullscreen)
            document.msExitFullscreen();
    }

    // Just to be sure...
    function isFullscreen() {
        var wkit;
        if (document.webkitIsFullScreen !== undefined)
            wkit = document.webkitIsFullScreen;
        else
            wkit = document.webkitFullscreenEnabled;
        return document.fullscreenEnabled || document.mozFullscreenEnabled
            || document.fullScreen || document.mozFullScreen || wkit
            || document.documentElement.fullscreenEnabled
            || document.documentElement.mozFullscreenEnabled
            || document.documentElement.webkitFullscreenEnabled
            || document.documentElement.fullScreen
            || document.documentElement.mozFullScreen
            || document.documentElement.webkitIsFullScreen;
    }

    function onFullScreen() {
        var iwin = document.getElementById('cframe').contentWindow;
        var p = $(iwin.document.body).parent();
        var state = isFullscreen();
        if (state)
            p.addClass("is-fullscreen");
        else
            p.removeClass("is-fullscreen");
        iwin.fireFullscreenChanged(state);
    }

    function applyListener(el) {
        el.addEventListener('webkitfullscreenchange', onFullScreen);
        el.addEventListener('mozfullscreenchange', onFullScreen);
        el.addEventListener('fullscreeneventchange', onFullScreen);
        el.addEventListener("MSFullscreenChange", onFullScreen);
    }

    this.FullScreen = {
        init: function() {
            iframe_html = $(document.getElementById('cframe').contentWindow.document.body).parent();
            applyListener(document.documentElement);
            applyListener(document);
        },

        toggle: function () {
            if (isFullscreen())
                cancelFullScreen();
            else
                requestFullScreen(document.documentElement);
        },

        applyIFrameClass: function() {
            onFullScreen();
        }
    };
}).call(this);
