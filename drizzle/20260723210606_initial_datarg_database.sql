CREATE TABLE `datasets` (
	`id` text PRIMARY KEY NOT NULL,
	`file_name` text NOT NULL,
	`content_sha256` text NOT NULL,
	`row_count` integer NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `datasets_file_name_unique` ON `datasets` (`file_name`);--> statement-breakpoint
CREATE TABLE `observations` (
	`series_id` text NOT NULL,
	`period` text NOT NULL,
	`frequency` text NOT NULL,
	`value` real NOT NULL,
	`unit` text NOT NULL,
	`status` text NOT NULL,
	`source_id` text NOT NULL,
	`source_url` text NOT NULL,
	`source_sha256` text NOT NULL,
	`retrieved_at` text NOT NULL,
	`ingested_at` text NOT NULL,
	PRIMARY KEY(`series_id`, `period`),
	FOREIGN KEY (`series_id`) REFERENCES `series`(`id`) ON UPDATE cascade ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `observations_period_idx` ON `observations` (`period`);--> statement-breakpoint
CREATE INDEX `observations_retrieved_at_idx` ON `observations` (`retrieved_at`);--> statement-breakpoint
CREATE TABLE `series` (
	`id` text PRIMARY KEY NOT NULL,
	`dataset_id` text NOT NULL,
	`frequency` text NOT NULL,
	`unit` text NOT NULL,
	`source_id` text NOT NULL,
	`source_url` text NOT NULL,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL,
	FOREIGN KEY (`dataset_id`) REFERENCES `datasets`(`id`) ON UPDATE cascade ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `series_dataset_id_idx` ON `series` (`dataset_id`);