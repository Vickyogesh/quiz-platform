$("#page-student").bind("pageinit", function() {
  function layout_grid(id) {
      aux_layoutGrid(id);
      var p = $(id).parent();
      var pw = p.width();
      var ph = p.height();
      var grid = $(id);

      ph -= 30; // Content margin.
      ph -= 10; // Button margin.

      if (pw > ph)
          ph /= 2;
      else
          ph /= 3;
      $(id + " .rect-button").css("height", ph + "px");
      $(id + " .rect-button").css("line-height", ph + "px");
  }

    function saveFbId(userId) {
        var data = {userId: userId};
        $.mobile.loading("show");
        aux_postJSON("/v1/link_facebook", data, function (data) {
            $.mobile.loading("hide");
            if (data.status != 200) {
                // Can't link Facebook account
                aux_showError("Impossibile collegare l'account Facebook");
            }
            else {
                sessionStorage.setItem('quiz_fbid', userId);
                fb_set_user_pic("#fbpic");
                $("#page-student #footer").hide();
                // acc linked.
                aux_showError(
                    "Il tuo account Facebook è stato collegato con successo!",
                    "Facebook");
            }
        });
    }

  $("#page-student #bttLogout").click(function() {
      window.name = null;
      $.mobile.loading("show");
      $.ajax("/v1/authorize/logout").always(function() {
          aux_deleteServicesCookies();
          $.mobile.loading("hide");
          $.mobile.changePage("#page-login");
      });
  });

  $("#page-student #bttFbLink").click(function() {
      FB.login(function(response) {
          if (response.status === 'connected') {
              console.log("connected");
              saveFbId(response.authResponse.userID);
          } else if (response.status === 'not_authorized') {
              // The person is logged into Facebook, but not our app.
              // So we do nothing.
              console.log("not connected");
          } else {
              // The person is not logged into Facebook, do nothing.
              console.log("not login");
          }
      }, {scope: 'publish_actions'});
  });

  $("#page-student").bind('pageshow', function() {
      $("#page-student h1").html(window.name);
      $("#page-student").page();
      layout_grid("#menugrid");
  });
  $("#page-student").bind('orientationchange', function() {
      layout_grid("#menugrid");
  });

  layout_grid("#menugrid");

  var resizeTimer;
  $(window).resize(function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function(){ layout_grid("#menugrid"); }, 100);
  });

  $("#page-student").bind('pageshow', function() {
      var fb_id = sessionStorage.getItem('quiz_fbid');
      console.log("fb_id0", fb_id);
      if (!fb_id || 0 === fb_id.length) 
          $("#page-student #footer").show();
      else {
          fb_set_user_pic("#fbpic");
      }
  });

});
