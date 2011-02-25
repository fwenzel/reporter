ALTER TABLE `theme` ADD `channel` VARCHAR( 20 ) NOT NULL AFTER `product` ;
ALTER TABLE `theme` ADD INDEX ( `channel` ) ;
