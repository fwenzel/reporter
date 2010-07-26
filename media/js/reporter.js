/* Feedback pages */
$(document).ready(function() {
    if (!$('#feedback').length) return;

    $('#id_add_url').change(function() {
        if (this.checked) {
            $('#id_url').removeAttr('disabled');
        } else {
            $('#id_url').attr('disabled', true);
        }
    }).change();

    var minlength = function() {
        if ($(this).hasClass('placeholder') ||
            $(this).val().length < $(this).attr('data-minlength')) {
            $('#feedbackform button').attr('disabled', true);
        } else {
            $('#feedbackform button').removeAttr('disabled');
        }
    };
    $('#id_description')
        .keyup(minlength)
        .change(minlength)
        .change()
        .focus();
});

/* Dashboard */
$(document).ready(function() {
    if (!$('#dashboard').length) return;

    var lang = $('html').attr('lang');

    var loading = function(that) {
        $(that).html('')
            .addClass('ajax_loading')
            .show();
    };
    var not_loading = function(that) {
        $(that).removeClass('ajax_loading');
    };
    var grab_ajax = function(what, callback, type) {
        var period = $('#id_period').val();
        if (!type) var type = 'json';
        $.get('/'+lang+'/dashboard/ajax/'+what+'/'+period, callback, type);
    };
    var init_all = function() {
        reload_all();
        messages.init();
    };
    var reload_all = function() {
        sentiment.init();
        trends.init();
        demo.init();
    };

    var sentiment = {
        container: $('#sentiment .ajaxy'),
        emos: ['total', 'happy', 'sad'],

        init: function() {
            loading(this.container);
            grab_ajax('sentiment', this.update, 'html');
        },

        update: function(data) {
            not_loading(sentiment.container);
            sentiment.container.html(data);
        }
    };

    var trends = {
        container: $('#trends .ajaxy'),

        init: function() {
            loading(this.container);
            grab_ajax('trends', this.update, 'html');
        },

        update: function(data) {
            not_loading(trends.container)
            trends.container.html(data);
        }
    };

    var demo = {
        container: $('#demo .ajaxy'),

        init: function() {
            loading(demo.container);
            grab_ajax('demographics', this.update, 'html');
        },

        update: function(data) {
            not_loading(demo.container)
            demo.container.html(data);
        }
    };

    var messages = {
        container: $('#messages .ajaxy'),

        init: function() {
            loading(messages.container);
            $.get('/'+lang+'/dashboard/ajax/messages', messages.update, 'html');
        },

        update: function(data) {
            not_loading(messages.container);

            messages.container.html(data);
            $(messages.container).show_opinion_meta();
        }
    }

    $('#id_period').change(reload_all);

    $('#overview,#messages').show();

    init_all();
    // update messages periodically
    setInterval(messages.init, 5 * 60 * 1000);
});

/* Mobile Dashboard/Search accordions */
$(document).ready(function() {
    if ($('.mobile#dashboard,.mobile#search').length == 0) return;

    $('#overview h2 a').click(function(e) {
        e.preventDefault();
        $('#overview .accordion').addClass('hidden');
        $(this).parent().siblings('.accordion').removeClass('hidden');
        $(this).blur();
    });
});

/* Search Forms */
$(document).ready(function() {
    if ($('#search_form').length == 0) return;

    var the_form = $('#search_form form'),
        search_adv = $('#search_adv'),
        adv_link_box = $('#show_search_adv'),
        adv_link = $('#show_search_adv a');

    adv_link.click(function(e) {
        e.preventDefault();
        $(this).blur();

        adv_link_box.toggleClass('active');
        search_adv.toggle();
    });
    adv_link_box.show();

    // no advanced options chosen? close the box.
    if (search_adv.find(':input[value!=""]').length == 0) {
        search_adv.hide();
        adv_link_box.removeClass('active');
    }

    // only submit non-empty fields
    the_form.submit(function() {
        the_form.find(':input[value=""]:not(button)').attr('disabled', true);
    });

    // show correct versions when product changes
    $('#id_product').change(function() {
        var prod = $(this).val(),
            versions = JSON.parse(the_form.attr('data-versions')),
            ver_select = $('#id_version');;
        ver_select.html('');
        for (i in versions[prod]) {
            var v = versions[prod][i],
                opt = $('<option/>').val(v[0]).text(v[1]);
            ver_select.append(opt);
        }
    });
});

/* search results page */
$(document).ready(function () {
    if ($('body#search').length == 0) return;
    $('#results').show_opinion_meta();
});

/* Bind click events for URL/UA metadata. */
jQuery.fn.show_opinion_meta = function() {
    $(this).find('.msg').each(function() {
        var msg = $(this);
        // URL
        msg.find('a.url').click(function(e) {
            e.preventDefault();
            msg.find('.urlpreview').toggle();
            $(this).blur();
        });
        msg.find('.urlpreview input').click(function() {
            $(this).select();
        });

        // UA
        msg.find('a.ua').click(function(e) {
            e.preventDefault();
            msg.find('.uapreview').toggle();
            $(this).blur();
        });
    });
}
