/* Sites dashboard */
$(document).ready(function() {
    if (!$('#website_issues').length) return;

    $(".more a").click(function(e) {
        e.preventDefault();
        var li = e.target.parentNode;
        $(".extra", li.parentNode ).fadeIn();
        $(li).toggleClass("less");
        return false;
    });

    var cluster_id_matcher = /\bcluster-(\d+)\b/;
    var expanded_cluster = null;
    var expanded_id = $("#results").attr("data-expanded-cluster");
    if (expanded_id != "") {
        expanded_cluster = document.getElementById("cluster-" + expanded_id);
    }
    var clusters_url = $("#results").attr("data-clusters-url");

    $(".show_similar, .hide_similar").click(function(e) {
        var h4 = e.target.parentNode;
        var cluster = h4.parentNode;
        if (expanded_cluster) {
            $("ol", expanded_cluster).slideUp();
            $(".hide_similar", expanded_cluster).hide();
            $(".show_similar", expanded_cluster).show();
        }
        if (cluster == expanded_cluster) return false;

        expanded_cluster = cluster;
        var cluster_id = cluster.id.substring("cluster-".length);
        var url = clusters_url.replace(/0$/, cluster_id);
        $(".hide_similar", cluster).show();
        $(".show_similar", cluster).hide();
        $("ol", cluster).addClass("ajax_loading").slideDown().load(
            url,
            function() {
                var list = $("ol", cluster);
                list.removeClass("ajax_loading").addClass("ajax_loaded");
                if (list.children().length < 4) {
                    list.css("overflow: show");
                }
                list.css("max-height", "21px");
                list.animate({"max-height": "117px"});
            }
        );
        return false;
    });
});
