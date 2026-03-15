
these are steps for extracting your friend list from facebook:
first: visit https://www.facebook.com/friends/list and scroll deep down to the bottom
then head to the console and paste the below script:

```js
var exportObj = [];
var accumulated = "";

for (var el of document.querySelectorAll('[data-visualcompletion="ignore-dynamic"]')) {
  var name = el.getAttribute("aria-label");
  if (name != null && name != "null") {
    exportObj.push({ name: name, profileURL: accumulated });
    accumulated = "";
  } else {
    var a = el.getElementsByTagName("a")[0];
    if (a) {
      accumulated += a.getAttribute("href");
    }
  }
}

// Newline added after each closing curly brace
var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportObj, null, 2));

var downloadAnchorNode = document.createElement('a');
downloadAnchorNode.setAttribute("href", dataStr);
downloadAnchorNode.setAttribute("download", "friendsList.json");
document.body.appendChild(downloadAnchorNode);
downloadAnchorNode.click();
downloadAnchorNode.remove();
```

here is the credit: https://stackoverflow.com/questions/50095522/how-to-get-whole-facebook-friends-list-from-api