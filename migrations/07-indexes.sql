ALTER TABLE feedback_opinion ADD KEY `cpvp` (`created`, `product`,`version`,
`positive`);
ALTER TABLE feedback_opinion ADD KEY `product` (`product`,`version`);
ALTER TABLE feedback_opinion ADD KEY `cpv` (`created`, `product`, `version`);
CREATE INDEX p ON theme (platform);
CREATE INDEX np ON theme (num_opinions, product);
CREATE INDEX ts ON theme_item (theme_id, score);
