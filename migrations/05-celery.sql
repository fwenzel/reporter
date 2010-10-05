BEGIN;
CREATE TABLE `celery_taskmeta` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `task_id` varchar(255) NOT NULL UNIQUE,
    `status` varchar(50) NOT NULL,
    `result` longtext,
    `date_done` datetime NOT NULL,
    `traceback` longtext
)
;
CREATE TABLE `celery_tasksetmeta` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `taskset_id` varchar(255) NOT NULL UNIQUE,
    `result` longtext NOT NULL,
    `date_done` datetime NOT NULL
)
;
COMMIT;
