(function($) {
    $.fn.fadeShow = function(dur, cb) {
        return this.animate({ 'height': 'show' }, dur, 'linear')
                   .animate({ 'opacity': 1 }, dur, 'linear', cb);
    };

    $.fn.fadeHide = function(dur, cb) {
        return this.animate({ 'opacity': 0 }, dur, 'linear')
                   .animate({ 'height': 'hide' }, dur, 'linear', cb);
    };


    $.fn.fadeToggle = function(dur, cb) {
        return this.queue(function() {
            var self = $(this);
            if (self.is(':visible')) {
                self.fadeHide(dur, cb);
            } else {
                self.fadeShow(dur, cb);
            }
            self.dequeue();
        });
    };


    $.fn.collapsible = function() {
        return this.click(function(e) {
            if ($(e.target).closest('.toggle').length == 0) {
                return;
            }

            var self = this;
            $(self).children('div, ul').fadeToggle(125, function() {
                $(self).toggleClass('collapsed');
            });

            return false;
        });
    };

    $.fn.barValue = function() {
        var text = $('em', this).html();
        return parseInt( text.replace(/\D+/, '') );
    },

    $.fn.bars = function() {
        return this.each(function() {
            var max = 1;
            var total = parseInt( $(this).attr('data-total') ) || 0;
            var bars = $('.bar', this);

            bars = bars.map(function() {
                var elem = $(this);
                var val = parseInt( elem.attr('data-value') ) || 0;
                var pretty = elem.attr('data-value-pretty') || val;
                max = Math.max(max, val);
                return { elem: elem, val: val, pretty: pretty };
            });

            bars.each(function() {
                var p = 100 * this.val / max;
                var meta = ' <span class="bg" style="width: ' + p + '%"></span>' +
                           '<span class="count">' + this.pretty + '</span>';

                if (total) {
                    var perc = (100 * this.val / total).toFixed();
                    meta = meta + ' <span class="perc">' + perc + '%</span>';
                }

                this.elem.append(meta);
            });
        });
    };


    $.fn.filters = function() {
        this.find('input[type=checkbox]').click(doSubmit);
        this.find('select').change(doSubmit);
        return this;

        function doSubmit(e) {
            e.preventDefault();

            var selected_product = $("#product").attr('data-selected')
            if (selected_product && selected_product != $("#product").val()) {
                var product = $('#product').val(),
                    versions = JSON.parse($('#product').attr('data-versions'))[product],
                    latest = $('#product option:selected').attr('data-latest');
                $('#product').attr('data-selected', product);
                // Fix versions list.
                $('#version option').remove();
                for (v in versions) {
                    $('#version').append(
                        $('<option>')
                            .val(versions[v][0])
                            .text(versions[v][1]))
                }
                $("#version").val(latest);
            }

            $(e.currentTarget).closest('form').submit();
        }
    };


    $.fn.choices = function() {
        return this.click(function(e) {
            var choice = $(e.target).closest('a');
            if (choice.length) {
                choice.closest('ul').find('a').removeClass('selected');
                choice.addClass('selected');
            }
        });
    };


    $(document).ready(function() {
        $('.collapsible').collapsible();

        $('#filters').filters().choices();

        $('#when a').click(function(e) {
            var customElem = $('#custom-date');
            if ( $(this).is('#show-custom-date') ) {
                customElem.fadeShow(125);
                e.preventDefault();
            } else {
                customElem.fadeHide(125);
            }
        });

        $('.message .options > a').click(function(e) {
            e.preventDefault();
        });
        $('.bars').bars();
    });

})(jQuery);
