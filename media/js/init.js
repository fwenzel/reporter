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
