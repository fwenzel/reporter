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

    $('#id_period').change(init_all);

    $('#search,#overview,#messages').show();

    init_all();
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
