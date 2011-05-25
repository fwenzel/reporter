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


    $(document).ready(function() {
        $('.collapsible').collapsible();
        $('#filters').filters();
		
		$('#tabs a').live('click', function(e) {
			$('.section').hide();
			$($(this).attr('href')).show();
			
			$('#tabs a').removeClass('selected');
			$(this).addClass('selected').blur();
			
			return false;
		});
		
		// Activate the first tab
		$('#tabs a:first').click();
		
		// Scroll past the browser's location bar in iOS/Firefox for Android
		window.scrollTo(0, 1);
    });

})(jQuery);
