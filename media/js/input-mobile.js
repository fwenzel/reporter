(function($) {
    $.fn.collapsible = function() {
        return this.click(function(e) {
            if ( !$(e.target).closest('.toggle').length ) {
                return;
            }

            $(this).toggleClass('collapsed')
            return false;
        });
    };
    $.fn.filters = function() {
        this.find('input[type=checkbox]').click(doSubmit);
        this.find('select').change(doSubmit);
        return this;

        function doSubmit(e) {
            $(e.currentTarget).closest('form').submit();
            return false;
        }
    };


    $(document).ready(function() {
        $('.collapsible').collapsible();
        $('#filters').filters();

        $('#header ul a').click(function(e) {
            var clicked = $(this);
            clicked.parent().siblings('li').find('a').each(function() {
                var tohide = $(this);
                tohide.removeClass('selected');
                $(tohide.attr('href')).hide();
            });
            clicked.addClass('selected');
            $(clicked.attr('href')).show();
        }).first().click();

        var hash = window.location.hash,
            subpage = $('#header a[href$='+hash+']').first();
        if (!subpage)
            subpage = $('#header ul a:first');
        subpage.click();
    });

})(jQuery);
