ALTER TABLE `theme` ADD `channel` VARCHAR( 20 ) NOT NULL AFTER `product`, ADD INDEX ( `channel` ) ;
