var input_chart; // Highcharts wants this to be global.

(function($) {

    var chart_me = function(chart_id, options) {
        $(document).ready(function() {
            options = options || {}
            var chart_div = $('#' + chart_id);
            if (!chart_div.length) return;

            var chart_data = JSON.parse(chart_div.attr('data-chart-config'));
            var tooltip_fmt = chart_div.attr('data-tooltip');
            var time_fmt = chart_div.attr('data-timeformat');
            var time_fmt_short = chart_div.attr('data-timeformat-short');
            var x_categories = chart_div.attr('data-categories');
            if (x_categories) {
                options.xAxis = {categories: JSON.parse(x_categories)};
            }


            input_chart = new Highcharts.Chart({
                colors: options.colors || ['#72B53E', '#BD5653', '#edd860'],
                chart: {
                    renderTo: chart_id,
                    defaultSeriesType: options.type || 'line',
                    margin: options.margin || [25, 25, 60, 45]
                },
                legend: options.legend || { y: 5 },
                title: {text: null},
                tooltip: options.tooltip || {
                    formatter: function() {
                        d = Highcharts.dateFormat(time_fmt, this.x * 1000)
                        return format(tooltip_fmt,
                                      {day: '<strong>' + d + '</strong>',
                                       num: '<strong>' + this.y + '</strong>'});
                    }
                },
                xAxis: options.xAxis || {
                    title: { text: null },
                    type: 'datetime',
                    labels: {
                        formatter: function() {
                            return Highcharts.dateFormat(time_fmt_short,
                                                         this.value * 1000);
                        }
                    },
                    plotBands: chart_data.plotBands || {}
                },
                yAxis: options.yAxis || {
                    title: { text: null },
                    min: 0,
                    tickPixelInterval: 40,
                    minorTickInterval: 500,
                    minorGridLineColor: "rgba(0, 0, 0, .1)"
                },
                plotOptions: options.plotOptions || {},
                series: chart_data.series,
                credits: { enabled: false }
            }); // input_chart


        });
    }

    chart_me('feedback-chart');
    var r_opts = {
        type: 'column', tooltip: {}, legend: {enabled: false},
        colors: ['#D73027', '#FC8D59', '#FEE08B', '#91CF60', '#1A9850'],
        plotOptions: { series: {borderWidth: 0, shadow: false}}

    };
    chart_me('ratings-chart', r_opts);

    var opts = {
        margin: [],
        colors: ['#55c4dd'],
        legend: {enabled: false},
        plotOptions: { series: {shadow: false, marker: {radius: 2.5}}},
        yAxis: {
            title: { text: null },
            min: 1,
            max: 5,
            allowDecimals: false,
            endOnTick: false,
            startOnTick: false,
            tickInterval: 1
        }
    }
    chart_me('startup-chart', opts);
    chart_me('pageload-chart', opts);
    chart_me('responsive-chart', opts);
    chart_me('crashy-chart', opts);
    chart_me('features-chart', opts);



    /** Show "welcome" block on first visit */
    $(document).ready(function() {
        if (!$.cookie('intro_seen')) {
            $('#welcome').show();
            $.cookie('intro_seen', true, {path: '/'});
        }
    });

})(jQuery);

