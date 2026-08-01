CREATE TABLE `yield_curve_instruments` (
	`dataset_id` text NOT NULL,
	`snapshot_date` text NOT NULL,
	`ticker` text NOT NULL,
	`instrument_name` text NOT NULL,
	`curve_type` text NOT NULL,
	`instrument_type` text NOT NULL,
	`settlement_date` text NOT NULL,
	`maturity_date` text NOT NULL,
	`days_to_maturity` integer NOT NULL,
	`price` real NOT NULL,
	`annual_yield` real NOT NULL,
	`monthly_yield` real NOT NULL,
	`duration_years` real NOT NULL,
	`volume` real NOT NULL,
	`status` text NOT NULL,
	`source_id` text NOT NULL,
	`source_url` text NOT NULL,
	`source_sha256` text NOT NULL,
	`retrieved_at` text NOT NULL,
	`ingested_at` text NOT NULL,
	PRIMARY KEY(`snapshot_date`, `ticker`),
	FOREIGN KEY (`dataset_id`) REFERENCES `datasets`(`id`) ON UPDATE cascade ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `yield_curve_dataset_id_idx` ON `yield_curve_instruments` (`dataset_id`);--> statement-breakpoint
CREATE INDEX `yield_curve_snapshot_type_maturity_idx` ON `yield_curve_instruments` (`snapshot_date`,`curve_type`,`maturity_date`);