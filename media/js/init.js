/* general initialization */
$(document).ready(function(){
    // Set up input placeholders.
    $('input[placeholder]').placeholder();
});

/* Feedback pages */
$(document).ready(function() {
    if (!$('#feedback').length) return;

    $('#id_add_url').change(function() {
        if (this.checked) {
            $('#id_url').removeAttr('disabled');
        } else {
            $('#id_url').attr('disabled', 'disabled');
        }
    }).change();

    $('#id_description').focus();
});

/* Dashboard */
$(document).ready(function() {
    if (!$('#dashboard').length) return;

    var loading = function(that) {
        $(that).html('')
            .addClass('ajax_loading')
            .show();
    };
    var not_loading = function(that) {
        $(that).removeClass('ajax_loading');
    };
    var grab_json = function(what, callback) {
        $.getJSON('/dashboard/ajax/'+what,
            {period: $('#id_period').val()}, callback
        );
    };
    var init_all = function() {
        sentiment.init();
        trends.init();
        demo.init();
    };

    var sentiment = {
        container: $('#sentiment .ajaxy'),
        emos: ['total', 'happy', 'sad'],

        init: function() {
            loading(this.container);
            grab_json('sentiment', this.update);
        },

        update: function(data) {
            proto = $('#sentiment .prototype').clone();
            if (data.sad > data.happy) {
                proto.find('.emotion.happy').remove();
            } else {
                proto.find('.emotion.sad').remove();
            }
            for (i in sentiment.emos) {
                var emo = sentiment.emos[i];
                var bar = proto.find(format('.response.{0}', [emo]));
                bar.text(format(bar.text(), [data[emo]]));
                if (emo != 'total' && data[emo] > 0)
                    bar.css('width', data[emo] / data['total'] * 75 + '%');
                else if (data[emo] == 0)
                    bar.css('width', '0');
                else
                    bar.css('width', '75%');
            }
            not_loading(sentiment.container);
            sentiment.container.html(proto.html());
        }
    };

    var trends = {
        container: $('#trends .ajaxy'),

        init: function() {
            loading(this.container);
            grab_json('trends', this.update);
        },

        update: function(data) {
            not_loading(trends.container)
            for (i in data.terms) {
                var term = data.terms[i];
                term_html = $(format('<span class="term w{weight}">{term}</span>', term));
                trends.container.append(term_html);
            }
        }
    };

    var demo = {
        container: $('#demo .ajaxy'),

        init: function() {
            loading(this.container);
            grab_json('demographics', this.update);
        },

        update: function(data) {
            not_loading(demo.container)

            var proto = $('#demo .prototype').clone(),
                os_proto = proto.find('dl.oses'),
                os_item = os_proto.find('dd');
            for (i in data.os) {
                var item = data.os[i],
                    target = os_item.clone();
                target.html(format(target.html(), item));
                os_proto.append(target);
            }
            os_item.remove();

            var loc_proto = proto.find('dl.locales'),
                loc_item = loc_proto.find('dd');
            for (i in data.locale) {
                var item = data.locale[i],
                    target = loc_item.clone();
                target.html(format(target.html(), item));
                loc_proto.append(target);
            }
            loc_item.remove();

            demo.container.html(proto.html());
        }
    };

    var messages = {
        container: $('#messages .ajaxy'),

        init: function() {
            loading(messages.container);
            $.getJSON('/dashboard/ajax/messages', {}, messages.update);
        },

        update: function(data) {
            not_loading(messages.container);

            var proto = $('#messages .prototype'),
                li_proto = proto.find('li'),
                ul = $('<ul>');
            for (i in data.msg) {
                var item = data.msg[i],
                    target = li_proto.clone();
                target.addClass(item.class);
                target.html(format(target.html(), item));
                if (item.url)
                    target.find('a').attr('href', item.url);
                else
                    target.find('a').remove();
                ul.append(target);
            }
            messages.container.html(ul);
            messages.update_url_previews();
        },

        update_url_previews: function() {
            messages.container.find('a.url').toggle(function(e) {
                e.preventDefault();
                var preview = $('#messages .prototype .urlpreview').clone(),
                    link = $(this);
                preview
                    .find('input').val(link.attr('href')).end()
                    .find('a').attr('href', link.attr('href')).end()
                    .hide()
                    .appendTo($(this).parent())
                    .slideDown();
            }, function(e) {
                e.preventDefault();
                $(this).siblings('.urlpreview').slideUp(function () {
                    $(this).remove();
                });
            });
        }
    }

    $('#id_period').change(init_all);

    $('#search,#overview,#messages').show();

    init_all();
    // update messages periodically
    messages.init();
    setInterval(messages.init, 5 * 60 * 1000);
});

/* Fake the placeholder attribute since Firefox doesn't support it.
 * (Borrowed from Zamboni) */
jQuery.fn.placeholder = function() {
    /* Bail early if we have built-in placeholder support. */
    if ('placeholder' in document.createElement('input')) {
        return this;
    }
    return this.focus(function() {
        var $this = $(this),
            text = $this.attr('placeholder');

        if ($this.val() == text) {
            $this.val('').removeClass('placeholder');
        }
    }).blur(function() {
        var $this = $(this),
            text = $this.attr('placeholder');

        if ($this.val() == '') {
            $this.val(text).addClass('placeholder');
        }
    }).each(function(){
        /* Remove the placeholder text before submitting the form. */
        var self = $(this);
        self.closest('form').submit(function() {
            if (self.hasClass('placeholder')) {
                self.val('');
            }
        });
    }).blur();
};

/* Python(ish) string formatting:
 * >>> format('{0}', ['zzz'])
 * "zzz"
 * >>> format('{x}', {x: 1})
 * "1"
 */
var format = function(s, args) {
    var re = /\{([^}]+)\}/g;
    return s.replace(re, function(_, match){ return args[match]; });
}
