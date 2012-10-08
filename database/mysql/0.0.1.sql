
CREATE TABLE IF NOT EXISTS `pyslicer_jobstatus` (
  `jobstatus_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `remoteprocessing_job_id` bigint(20) NOT NULL,
  `event_id` int(10) NOT NULL,
  `notify_date` timestamp NULL DEFAULT NULL ,
  `event_type` text,
  `message` text,
  PRIMARY KEY (`jobstatus_id`)
);