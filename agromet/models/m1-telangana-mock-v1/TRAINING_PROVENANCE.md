# M1 Training Provenance

Model: `m1-telangana-mock-v1`

This bundle was trained from the mock/synthetic dataset structure supplied for SIH26074:
- AWS observations generated from the provided development generator pattern
- block forecast inputs generated for the Chevella/Rangareddy pilot
- supplied Panchayat registry
- supplied SRTM-derived terrain attributes

The data are NOT official TGDPS/IMD observations and the metrics are NOT production Telangana performance results.

The small-demo temporal partition override was used because the supplied 30-day mock window is smaller than the production trainer's default minimum of 30 rows per fit/calibration/holdout partition.

For production training, use a sufficiently long historical archive and remove the small-demo override.
