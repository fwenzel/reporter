
(function($) {
    $.extend($.fn, {
        nodeIndex: function() {
            var i = -1, node = this.get(0);
            for ( ; node; i++, node = node.previousSibling);
            return i;
        },
        
        switchTo: function(what, callback) {
            var fromElem = this,
            toElem = $(what),
            width = $(window).width();
            
            if (fromElem.nodeIndex() < toElem.nodeIndex()) {
                var fromEnd = -width;
                var toStart = width;
            } else {
                var fromEnd = width;
                var toStart = -width;
            }

            fromElem.css({ left: 0, right: 0 });
            toElem.addClass('entering')
                .css({ left: toStart, right: -toStart, display: 'block' });
            $('html').addClass('transitioning');
            
            toElem.one('transitionend', function(e) {
                fromElem.css({ display: 'none' });
                toElem.removeClass('entering');
                $('html').removeClass('transitioning');
                if (callback) callback();
            });
            
            setTimeout(function() {
                fromElem.css({ left: fromEnd, right: -fromEnd });
                toElem.css({ left: 0, right: 0 });
            }, 100);
            
            return this;
        },
        submitButton: function(state) {
            var textElem = this.find('span');
            var oldHTML = textElem.html();
            var newTextAttr = (state == 'waiting') ? 'data-waittext' : 'data-text';
            
            this.toggleClass('waiting', state == 'waiting');
            textElem.html( this.attr(newTextAttr) );
            
            if (state == 'waiting') this.attr('data-text', oldHTML);
            
            return this;
        },
        clickEnable: function(bindTo) {
            return this.each(function() {
                onClick.call(this);
                $(this).click(onClick);
            });
            
            function onClick() {
                var checked = this.checked;
                $(bindTo)[0].disabled = !checked;
            }
        }
    });

    
    var currentArticle;
    
    function getArticle(href) {
        var hash = (href || '').replace(/^.*#/, '') || 'intro';
        var elem = $('#'+hash);
        return elem.length ? elem : $('#intro');
    }
    
    function goToArticle(href, pushState, callback)
    {
        var oldArticle = currentArticle;
        var newArticle = getArticle(href);
        
        if (oldArticle.get(0) == newArticle.get(0)) {
            return;
        }

        if (pushState) window.history.pushState('', '', '#' + newArticle.attr('id'));
        currentArticle = newArticle;
        
        oldArticle.switchTo(newArticle, callback);
    }
    
    $(function() {
        // Look for errors and show that initially
        var errorlst = $('article .errorlist');
        if(errorlst.length) {
            currentArticle = errorlst.closest('article');
            currentArticle.css({ display: 'block' });
            window.location.hash = currentArticle.attr('id');
        }
        else {
            currentArticle = getArticle(document.location.hash);
            currentArticle.css({ display: 'block' });
        }

        window.onpopstate = function(e) {
            goToArticle(document.location.hash);
        };
        
        $('.submit a').click(function(e) {
            $(this).closest('form').submit();
            return false;
        });
        
        $('article form').submit(function(e) {
            var button = $(this).find('.submit a');
            button.submitButton('waiting');
        });

        $('#happy-with-url').clickEnable('#happy-url');
        $('#sad-with-url').clickEnable('#sad-url');
    });

    $('html').addClass('js');

})(jQuery);
