BEGIN;
CREATE TABLE `theme` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `pivot_id` integer NOT NULL,
    `num_opinions` integer NOT NULL,
    `feeling` varchar(20) NOT NULL,
    `platform` varchar(255) NOT NULL,
    `created` datetime NOT NULL
)
;
ALTER TABLE `theme` ADD CONSTRAINT `pivot_id_refs_id_7c9e77b1` FOREIGN KEY (`pivot_id`) REFERENCES `feedback_opinion` (`id`);
CREATE TABLE `theme_item` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `theme_id` integer NOT NULL,
    `opinion_id` integer NOT NULL,
    `score` double precision NOT NULL,
    `created` datetime NOT NULL
)
;
ALTER TABLE `theme_item` ADD CONSTRAINT FOREIGN KEY (`theme_id`) REFERENCES `theme` (`id`);
ALTER TABLE `theme_item` ADD CONSTRAINT FOREIGN KEY (`opinion_id`) REFERENCES `feedback_opinion` (`id`);
CREATE INDEX `theme_c360d361` ON `theme` (`pivot_id`);
CREATE INDEX `theme_af507caf` ON `theme` (`num_opinions`);
CREATE INDEX `theme_97bf82c4` ON `theme` (`feeling`);
CREATE INDEX `theme_eab31616` ON `theme` (`platform`);
CREATE INDEX `theme_3216ff68` ON `theme` (`created`);
CREATE INDEX `theme_item_1079d5be` ON `theme_item` (`theme_id`);
CREATE INDEX `theme_item_ac81e047` ON `theme_item` (`opinion_id`);
COMMIT;

