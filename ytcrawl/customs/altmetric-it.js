javascript: (
    (
        function () {
            var a;
            a = function () {
                var a, b, c, d, e;
                b = document, e = b.createElement("script"), a = b.body, d = b.location;
                try {
                    if (!a) throw 0; // a == b.body
                    c = "d1bxh8uas1mnw7.cloudfront.net";
                    if (typeof runInject != "function") return e.setAttribute("src", "" + d.protocol + "//" + c + "/assets/content.js?cb=" + Date.now()), e.setAttribute("type", "text/javascript"), e.setAttribute("onload", "runInject()"), a.appendChild(e)
                }
                catch (f) {
                    return console.log(f), alert("Please wait until the page has loaded.")
                }
            }, a(), void 0
        }
    )
).call(this);

// javascript:((function(){var a;a=function(){var a,b,c,d,e;b=document,e=b.createElement("script"),a=b.body,d=b.location;try{if(!a)throw 0;c="d1bxh8uas1mnw7.cloudfront.net";if(typeof runInject!="function")return e.setAttribute("src",""+d.protocol+"//"+c+"/assets/content.js?cb="+Date.now()),e.setAttribute("type","text/javascript"),e.setAttribute("onload","runInject()"),a.appendChild(e)}catch(f){return console.log(f),alert("Please wait until the page has loaded.")}},a(),void 0})).call(this);