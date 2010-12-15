/** JS Code for the feedback pages for stable Firefox versions. */

(function($) {
    $.extend($.fn, {
        nodeIndex: function() {
            var i = -1, node = this.get(0);
            for ( ; node; i++, node = node.previousSibling);
            return i;
        },

        switchTo: function(what, callback) {
            var fromElem = this,
                toElem = $(what);

            if (fromElem.nodeIndex() < toElem.nodeIndex()) {
                var height = fromElem.height();
                var fromEnd = 0 - height;
                var toStart = height;
            } else {
                var height = toElem.height();
                var fromEnd = height;
                var toStart = 0 - height;
            }

            fromElem.css({ top: 0, opacity: 1 });
            toElem.css({ top: toStart, opacity: 0, display: 'block' });
            $('html').addClass('transitioning');

            toElem.one('transitionend', function(e) {
                fromElem.css({ display: 'none' });
                $('html').removeClass('transitioning');
                if (callback) callback();
            });

            setTimeout(function() {
                fromElem.css({ top: fromEnd, opacity: 0 });
                toElem.css({ top: 0, opacity: 1 });
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

            this.blur();
            return this;
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
        currentArticle = getArticle(document.location.hash);
        currentArticle.css({ display: 'block' });

        window.onpopstate = function(e) {
            goToArticle(document.location.hash);
        };

        $('article form').submit(function(e) {
            var form = $(this),
                button = form.find('.submit a');

            e.preventDefault();

            form.find('.errorlist').remove();  // Wipe out previous errors.

            button.submitButton('waiting');

            $.ajax({
                type: 'POST',
                url: $(this).attr('action'),
                data: $(this).serialize(),
                dataType: 'json',
                success: function(data) {
                    form.find(':input:not(:hidden)').val('');
                    goToArticle('#thanks', true, function() {
                        button.submitButton('default');
                    });
                },
                error: function(xhr, status, error) {
                    try {
                        var errorlist = JSON.parse(xhr.responseText);
                        for (var i in errorlist) {
                            var target;
                            if (i == '__all__') {
                                target = button;
                            } else {
                                target = $('.error-target-'+i);
                            }
                            if (!target.length)
                                target = form.find(':input[name='+i+']');
                            var ul = $('<ul class="errorlist"/>');
                            for (e in errorlist[i]) {
                                ul.append($('<li>').text(errorlist[i][e]));
                            }
                            target.after(ul);
                        }
                    } catch (err) {
                        alert(xhr.responseText);
                    }
                    button.submitButton('default');
                }
            });
        });

        $('.submit a').click(function(e) {
            $(this).closest('form').submit();
            return false;
        });
    });

    $(document).ready(function() {
        // Submit on locale choice
        $('form.languages')
            .find('select').change(function(){
                this.form.submit();
            }).end()
            .find('button').hide();
    });

    document.documentElement.className += ' js';
})(jQuery);
