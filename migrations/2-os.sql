UPDATE feedback_opinion
    SET os='winxp' WHERE os='win' AND user_agent LIKE '%Windows NT 5.1%';
UPDATE feedback_opinion
    SET os='vista' WHERE os='win' AND user_agent LIKE '%Windows NT 6.0%';
UPDATE feedback_opinion
    SET os='win7' WHERE os='win' AND user_agent LIKE '%Windows NT 6.1%';

