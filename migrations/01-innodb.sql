CREATE TABLE `feedback_cluster` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `type_id` int(11) NOT NULL,
  `pivot_id` int(11) NOT NULL,
  `num_opinions` int(11) NOT NULL,
  `created` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `feedback_cluster_777d41c8` (`type_id`),
  KEY `feedback_cluster_c360d361` (`pivot_id`),
  KEY `feedback_cluster_af507caf` (`num_opinions`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `feedback_clusteritem`
--

CREATE TABLE `feedback_clusteritem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cluster_id` int(11) NOT NULL,
  `opinion_id` int(11) NOT NULL,
  `score` double NOT NULL,
  `created` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `feedback_clusteritem_2777883f` (`cluster_id`),
  KEY `feedback_clusteritem_ac81e047` (`opinion_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `feedback_clustertype`
--

CREATE TABLE `feedback_clustertype` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `feeling` varchar(20) NOT NULL,
  `platform` varchar(255) NOT NULL,
  `version` varchar(255) NOT NULL,
  `frequency` varchar(255) NOT NULL,
  `created` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `feeling` (`feeling`,`platform`,`version`,`frequency`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `feedback_cluster`
--
ALTER TABLE `feedback_cluster`
  ADD CONSTRAINT FOREIGN KEY (`pivot_id`) REFERENCES `feedback_opinion` (`id`),
  ADD CONSTRAINT FOREIGN KEY (`type_id`) REFERENCES `feedback_clustertype` (`id`);

--
-- Constraints for table `feedback_clusteritem`
--
ALTER TABLE `feedback_clusteritem`
  ADD CONSTRAINT FOREIGN KEY (`cluster_id`) REFERENCES `feedback_cluster` (`id`),
  ADD CONSTRAINT FOREIGN KEY (`opinion_id`) REFERENCES `feedback_opinion` (`id`);

ALTER TABLE feedback_opinion ENGINE=InnoDB;
