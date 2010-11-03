var feedback_chart; // Highcharts wants this to be global.

(function($) {
    $(document).ready(function() {
        var chart_id = 'feedback-chart',
            chart_div = $('#'+chart_id);
        if (!chart_div) return;
        var chart_data = JSON.parse(chart_div.attr('data-chart-config'));
        var tooltip_fmt = chart_div.attr('data-tooltip');
        var time_fmt = chart_div.attr('data-timeformat');
        var time_fmt_short = chart_div.attr('data-timeformat-short');

        feedback_chart = new Highcharts.Chart({
            colors: ['#72B53E', '#BD5653'],
            chart: {
                renderTo: chart_id,
                defaultSeriesType: 'line'
            },
            title: {text: null},
            tooltip: {
                formatter: function() {
                    d = Highcharts.dateFormat(time_fmt, this.x * 1000)
                    return format(tooltip_fmt,
                                  {day: '<strong>' + d + '</strong>',
                                   num: '<strong>' + this.y + '</strong>'});
                }
                },
            xAxis: {
                title: {
                    text: null
                },
                type: 'datetime',
                labels: {
                    formatter: function() {
                        return Highcharts.dateFormat(time_fmt_short,
                                                     this.value * 1000);
                    }
                }
            },
            yAxis: {
                title: {
                    text: null
                },
                min: 0,
                tickPixelInterval: 40,
                minorTickInterval: 500,
            },
            series: chart_data.series,
            credits: { enabled: false }
        });
    });

})(jQuery);
