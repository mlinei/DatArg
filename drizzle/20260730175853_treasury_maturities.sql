CREATE TABLE `treasury_maturities` (
	`dataset_id` text NOT NULL,
	`series_id` text NOT NULL,
	`snapshot_date` text NOT NULL,
	`period` text NOT NULL,
	`frequency` text NOT NULL,
	`service_type` text NOT NULL,
	`category` text NOT NULL,
	`detail_level` text NOT NULL,
	`source_row` integer NOT NULL,
	`instrument` text NOT NULL,
	`value` real NOT NULL,
	`unit` text NOT NULL,
	`status` text NOT NULL,
	`source_id` text NOT NULL,
	`source_url` text NOT NULL,
	`source_sha256` text NOT NULL,
	`retrieved_at` text NOT NULL,
	`ingested_at` text NOT NULL,
	PRIMARY KEY(`snapshot_date`, `service_type`, `source_row`, `period`),
	FOREIGN KEY (`dataset_id`) REFERENCES `datasets`(`id`) ON UPDATE cascade ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `treasury_maturities_dataset_id_idx` ON `treasury_maturities` (`dataset_id`);--> statement-breakpoint
CREATE INDEX `treasury_maturities_snapshot_period_idx` ON `treasury_maturities` (`snapshot_date`,`period`);