The way the database is designed, might benefit from an explanation so that it
does not appear arbitrary, and might be easier / more satisfying to work with:

The method is "dimensional modeling" (not traditional ER modeling, I *do* know
about normalization :), and is often used for analytics databases ("build
once, query often").

Basically, a row in the sitesummary table is not a website in any way. It
stands for "all clusters that share the same coordinates in the search space".

The search space has 4 "dimensions" in this case:
- version: e.g. "<day>", "<week>", "4.0b3"
- positive: True, False, None (= "Both")
- url: "http://google.com", "https://google.com"
- platform: "vista", "mac", "maemo", "android" or "<mobile>" (= maemo+android)

The other fields in the table (the so called "facts") are just precomputed
aggregate values over the matching comments / clusters. Now, of course a
cluster can be at multiple coordinates in the search space (yesterday's
comments are latest beta as well as last 7 days, and happy cómments are always
also "Both"), so it is aggregated into multiple sitesummary records. For this
reason, 'version', 'platform' and 'positive' always need to be specified in queries (urls do not need that, as they are disjunct).

In the future, a "locale" dimension could be added (where the "all"
coordinate-component maps 1:1 to the current site summaries), which would
allow to also cluster by locale, and filter by them.

So the reliable way to link to a search result is to use the actual search
parameters for *all* dimensions (e.g. with four get parameters, maybe with
defaults). This will also yield the most useful (if not the same) results if
the link is shared and reused in the future, and it will make for readable
urls.
The SiteSummary.id is intended to link clusters to their search coordinates
when making SQL queries, not to reference these search coordinates from the
web. Everytime the clusters are regenerated (every night) the site summary ids
will expire.

