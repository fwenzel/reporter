ALTER TABLE `website_issues_sitesummary`
    ADD COLUMN `os` varchar(30) DEFAULT NULL;
CREATE INDEX `sitesummary_eab31616`
    ON `website_issues_sitesummary` (`url`,`os`,`version`);