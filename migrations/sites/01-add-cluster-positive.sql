ALTER TABLE `website_issues_cluster`
    ADD COLUMN `positive` tinyint(1) NOT NULL DEFAULT 0;

-- Get rid of circular constraint on non-null columns so we can add rows using
-- django ORM.
ALTER TABLE `website_issues_cluster`
    MODIFY COLUMN `primary_comment_id` int(11) DEFAULT NULL;
