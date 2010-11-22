ALTER TABLE `feedback_opinion` ADD `manufacturer` VARCHAR( 255 ) NOT NULL AFTER `locale` ,
ADD `device` VARCHAR( 255 ) NOT NULL AFTER `manufacturer` ;

ALTER TABLE `feedback_opinion` ADD INDEX ( `manufacturer` , `device` ) ;
