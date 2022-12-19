var $j = jQuery.noConflict();

$j(document).on('click', '.add', function($) {
    var section = $j(this).data('id');
    $j.ajax({
        url: "/" + section + '/addSection/',
        method : 'POST',
        context: this,
        success: function(response) {
            $j(this).removeClass("add").addClass("remove");
            $j(this).html('Rem Section');
            
            // src: https://codepen.io/neolegolas14/pen/BeQydx
            var el = document.createElement("div");
            el.className = "notifs";
            var y = document.getElementById("notifs-container");
            el.innerHTML = response.message;
            y.append(el);
            el.className = "notifs show";
            setTimeout(function(){ el.remove(); }, 3000);
        },
        error: function(response) { 
            var el = document.createElement("div");
            el.className = "notifs";
            var y = document.getElementById("notifs-container");
            el.innerHTML = "Warning: " + response.responseJSON.error;
            y.append(el);
            el.className = "notifs show conflict";
            setTimeout(function(){ el.remove(); }, 3000);
        }
    });
});

$j(document).on('click', '.remove', function($) {
    var section = $j(this).data('id');
    $j.ajax({
    url: "/" + section + '/remSection/',
    method : 'POST',
    context: this,
    success: function(response) {
        $j(this).removeClass("remove").addClass("add");
        $j(this).html('Add Section');
        if ($j(this).hasClass("refresh")){
            location.reload();
        }

        // src: https://codepen.io/neolegolas14/pen/BeQydx
        var el = document.createElement("div");
        el.className = "notifs";
        var y = document.getElementById("notifs-container");
        el.innerHTML = response.message;
        y.append(el);
        el.className = "notifs show remove";
        setTimeout(function(){ el.remove(); }, 3000);
    },
    failure: function(response) { 
        alert('Failed to remove course!');
    }
    }); 
});


/*$j(window).on('load', function($) {   
    // src: https://stackoverflow.com/questions/19981304/how-to-reload-page-once-using-jquery
    if (!localStorage.getItem("reload")) {
        // set reload to true and then reload the page 
        localStorage.setItem("reload", "true");
        window.location.reload(true);
    }
    // after reloading remove "reload" from localStorage
    else {
        localStorage.removeItem("reload");
        //localStorage.clear(); // or clear it, instead
    }
});*/