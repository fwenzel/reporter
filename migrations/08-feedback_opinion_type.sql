ALTER TABLE `feedback_opinion` ADD `type` SMALLINT UNSIGNED NOT NULL DEFAULT 1 AFTER `positive`;
UPDATE `feedback_opinion` SET `type` = 2 WHERE `positive` = 0;
ALTER TABLE `feedback_opinion` DROP `positive`;
