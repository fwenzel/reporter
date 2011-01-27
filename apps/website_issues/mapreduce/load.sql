-- Execute the mysql client in the directory where you have put the tsvs.
-- You need to execute this for the db that website_issues routes to.
-- To generate tsvs from the mapreduce output, use normalize_to_tsv.py

set AUTOCOMMIT=0;
set CHARACTER_SET_CLIENT="utf8";
set foreign_key_checks=0;

begin;

truncate table website_issues_comment;

LOAD DATA LOCAL INFILE 'comments.tsv'
INTO TABLE website_issues_comment
FIELDS TERMINATED BY '\t' ESCAPED BY '\\' LINES TERMINATED BY '\n'
(id, cluster_id, description, opinion_id, score);


truncate table website_issues_cluster;

LOAD DATA LOCAL INFILE 'clusters.tsv'
INTO TABLE website_issues_cluster
FIELDS TERMINATED BY '\t' ESCAPED BY '\\' LINES TERMINATED BY '\n'
(id, site_summary_id, size, primary_description, primary_comment_id, positive);


truncate table website_issues_sitesummary;

LOAD DATA LOCAL INFILE 'sitesummaries.tsv'
INTO TABLE website_issues_sitesummary
FIELDS TERMINATED BY '\t' ESCAPED BY '\\' LINES TERMINATED BY '\n'
(id, url, version, @positive, @os, size, issues_count, praise_count)
set positive = IF(@positive="NULL", NULL, @positive),
    os = IF(@os="<desktop>",
            "<firefox>",
            IF(@os="NULL", NULL, @os));

commit;