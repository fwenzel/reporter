
(function() {
    function url_enabler(check, input) {
        check = document.getElementById(check),
        input = document.getElementById(input);
        
        if (!check || !input) return;
        
        input.disabled = !check.checked;
        
        check.addEventListener('click', function(e) {
            input.disabled = !check.checked;
        }, false);
    }
    
    function on_submit(e) {
        var target = e.target;  
        var btn = target.getElementsByTagName('button')[0];
        btn.disabled = true;    
    }

    document.addEventListener('submit', on_submit, false);
    url_enabler('happy-hasurl', 'happy-url');
    url_enabler('sad-hasurl', 'sad-url');

    var loc = window.location;
    var err = document.getElementById('errors');
    if(err) {
        loc.hash = err.value;
    }
    else if(loc.hash == '') {
        loc.hash = "intro";
    }
})();
