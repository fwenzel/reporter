(function($) {
    $.fn.collapsible = function() {
        return this.click(function(e) {
            if ( !$(e.target).closest('.toggle').length ) {
                return;
            }

            $(this).toggleClass('collapsed');
            return false;
        });
    };
    $.fn.filters = function() {
        function doSubmit(e) {
            $(e.currentTarget).closest('form').submit();
            return false;
        }

        this.find('input[type=checkbox]').click(doSubmit);
        this.find('select').change(doSubmit);
        return this;
    };
    $.fn.hideExtraFilters = function() {
        var filters = $(this).children('.filter');

        $(filters).addClass('expandable expanded');
        
        // If enough filters exist, show the "Show More X" link and
        // hide filters beyond the first four.
        if (filters.length) {
            $(this).children('.expand').show();
            $(this).children('.filter:nth-child(1n+5)')
                .removeClass('expanded');
        }
    };


    $(document).ready(function() {
		$('body').removeClass('no-js').addClass('js');
		
        $('.collapsible').collapsible();
        $('#filters').filters();
        $('#filters div ul').hideExtraFilters();
		
		$('#tabs a').live('click', function(e) {
			$('.section').hide();
			$($(this).attr('href')).show();
			
			$('#tabs a').removeClass('selected');
			$(this).addClass('selected').blur();
			
			return false;
		});
		
		// Listen for any "Show more X" filter links
		$('.expand-filters').live('click', function() {
		    $(this).closest('ul').children('.filter')
    		    .addClass('expanded');
    		$(this).parent('li').hide();
    		
    		return false;
		});
    });

})(jQuery);
