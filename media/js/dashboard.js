var feedback_chart; // Highcharts wants this to be global.

(function($) {
    $(document).ready(function() {
        var chart_id = 'feedback-chart',
            chart_div = $('#'+chart_id);
        if (!chart_div) return;
        var chart_data = JSON.parse(chart_div.attr('data-chart-config'));

        feedback_chart = new Highcharts.Chart({
            chart: {
                renderTo: chart_id,
                defaultSeriesType: 'line'
            },
            title: {
                text: chart_div.attr('data-title')
            },
            xAxis: {
                title: {
                    text: ''
                },
                categories: chart_data.categories
            },
            yAxis: {
                title: {
                    text: ''
                }
            },
            series: chart_data.series
        });
    });

})(jQuery);
