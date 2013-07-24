
function getCookie(Name){ //get cookie value
	var re=new RegExp(Name+"=[^;]+", "i"); //construct RE to search for target name/value pair
	if (document.cookie.match(re)) //if cookie found
		return document.cookie.match(re)[0].split("=")[1]; //return its value
		
	return "";
}

function setCookie(name, value, days){ //set cookie value
	var expireDate = new Date();
	//set "expstring" to either future or past date, to set or delete cookie, respectively
	var expstring=expireDate.setDate(expireDate.getDate()+parseInt(days));
	document.cookie = name+"="+value+"; expires="+expireDate.toGMTString()+"; path=/";
}

function deleteCookie(name) {
    document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:01 GMT;';
};

function deleteCookie(name, path, domain) {
   if (getCookie(name)) {
           document.cookie = name + "=" +
           ((path) ? "; path=" + path : "") +
           ((domain) ? "; domain=" + domain : "") +
           "; expires=Thu, 01 Jan 1970 00:00:00 GMT;"
   }
}

function doLogout() {
  window.qsid = null;
  window.name = null;
  deleteCookie('QUIZSID', '/');
  sessionStorage.removeItem("quizqsid");
  sessionStorage.removeItem("quizname");
  window.location = "index.html";
}
