$(document).ready(function () {
	
	$(document).ajaxError(function() {
		alert('Unexpected server response.');
		
		$('.cssSubmitButton').removeClass('loading');
	});
	
	doQuit();
    
    $('#button a').click(function () {
        
		var link = $(this);
		onAuth(link);
	});
	
	$('input').css('border','0px');
        
});

