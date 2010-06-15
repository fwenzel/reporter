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
    var grab_ajax = function(what, callback, type) {
        var period = $('#id_period').val();
        if (!type) var type = 'json';
        $.get('/dashboard/ajax/'+what+'/'+period, callback, type);
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
            $.get('/dashboard/ajax/messages', messages.update, 'html');
        },

        update: function(data) {
            not_loading(messages.container);

            messages.container.html(data);
            $(messages.container).show_url_previews();
        }
    }

    $('#id_period').change(reload_all);

    $('#overview,#messages').show();

    init_all();
    // update messages periodically
    setInterval(messages.init, 5 * 60 * 1000);
});

/* search forms */
$(document).ready(function() {
    if ($('#search_form').length == 0) return;

    var the_form = $('#search_form form'),
        search_adv = $('#search_adv'),
        adv_link = $('#show_search_adv');

    $('#search_links').show();

    adv_link.click(function(e) {
        e.preventDefault();
        search_adv.slideToggle();
    });

    if (search_adv.find(':input[value!=""]').length == 0)
        adv_link.click();

    the_form.submit(function() {
        // only submit non-empty fields
        the_form.find(':input[value=""]:not(button)').attr('disabled', true);
    });
});

/* search results page */
$(document).ready(function () {
    if ($('body#search').length == 0) return;
    $('#results').show_url_previews();
});

/* Bind click events for URL previews. */
jQuery.fn.show_url_previews = function() {
    $(this).find('a.url').toggle(function(e) {
        e.preventDefault();
        $(this).siblings('.urlpreview').slideDown();
        $(this).blur();
    }, function(e) {
        e.preventDefault();
        $(this).siblings('.urlpreview').slideUp();
        $(this).blur();
    });
    $(this).find('.urlpreview input').click(function() {
        $(this).select();
    });
}
