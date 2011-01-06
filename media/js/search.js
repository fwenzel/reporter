$(document).ready(function() {
    $('.filter a.more').click(function(e) {
        e.preventDefault();
        $(this).closest('li').hide()
        $('.extra', $(this).closest('ul')).show()
    });

});
