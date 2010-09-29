DROP TABLE theme;

CREATE TABLE `theme` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `pivot_id` integer NOT NULL,
    `num_opinions` integer NOT NULL,
    `feeling` varchar(20) NOT NULL,
    `product` smallint UNSIGNED NOT NULL,
    `platform` varchar(255) NOT NULL,
    `created` datetime NOT NULL
)
;
ALTER TABLE `theme` ADD CONSTRAINT `pivot_id_refs_id_d3ca7add` FOREIGN KEY (`pivot_id`) REFERENCES `feedback_opinion` (`id`);
