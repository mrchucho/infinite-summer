function createCookie(name,value,days) {
	if (days) {
		var date = new Date();
		date.setTime(date.getTime()+(days*24*60*60*1000));
		var expires = "; expires="+date.toGMTString();
	}
	else var expires = "";
	document.cookie = name+"="+value+expires+"; path=/";
}

function readCookie(name) {
	var nameEQ = name + "=";
	var ca = document.cookie.split(';');
	for(var i=0;i < ca.length;i++) {
		var c = ca[i];
		while (c.charAt(0)==' ') c = c.substring(1,c.length);
		if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
	}
	return null;
}

function eraseCookie(name) {
	createCookie(name,"",-1);
}

$(document).ready(function(){
    $('.first').focus();

    $('#graph').sparkline('html',{'type': 'tristate'});

    var flashMsg = readCookie('flash_message');
    if (flashMsg) {
        flashMsg = unescape(flashMsg);
        var el = $('<div id="flash-message">'+
          '<div id="flash-message-close">'+
          '<a title="dismiss this message" '+
          'id="flash-message-button" href="#">X</a></div>'+
          flashMsg + '</div>');
        $('a#flash-message-button', el).bind(
          'click', function () {
            $(this.parentNode.parentNode).remove();
        });
        $('#bd').prepend(el);
        eraseCookie('flash_message');
    } 
});
