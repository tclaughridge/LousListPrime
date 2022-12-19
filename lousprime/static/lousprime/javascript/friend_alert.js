var $j = jQuery.noConflict();

function get_friend_request(){
    var endpoint = $j("#social_url").attr("href");
    $j.ajax({
     url: endpoint+"friendrequestcount/",
     type: 'get',
     headers:{
        'X-Requested-With': 'XMLHttpRequest', //Necessary to check whether request is from ajax
     },
     success: function(response){
      // Perform operation on the return value
      var y = document.getElementById("friend_request_count");
      var social = document.getElementById("social_friend_request_count");
      if (response.friend_request_count > 0){
        y.innerHTML = response.friend_request_count;
        social.innerHTML = response.friend_request_count;
      }
      else{
        y.innerHTML = "";
        social.innerHTML = "";
      }
     }
    });
}

$j(document).ready(function(){
    get_friend_request();
    setInterval(get_friend_request,5000);
});