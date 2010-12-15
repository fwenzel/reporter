CREATE TABLE `feedback_rating` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `opinion_id` integer NOT NULL,
    `type` smallint UNSIGNED NOT NULL,
    `value` smallint UNSIGNED
) TYPE=innodb;
;
ALTER TABLE `feedback_rating` ADD CONSTRAINT `opinion_id_refs_id_36fb0fb1` FOREIGN KEY (`opinion_id`) REFERENCES `feedback_opinion` (`id`) ON DELETE CASCADE;
CREATE INDEX `opinion` ON `feedback_rating` (`opinion_id`);
CREATE INDEX `type` ON `feedback_rating` (`type`);
