# Post-Beta Health Integrations

## Purpose

Add Garmin, Oura Ring, and Apple Health after private beta feedback confirms
which data sources users actually need. Keep Strava-first users working while
expanding the provider graph.

## Integration Targets

- Garmin: activities, training load, and device workout history.
- Oura Ring: sleep, readiness, recovery, HRV, resting heart rate.
- Apple Health: Apple Watch/iPhone workouts and health samples.

## Design Requirements

- Normalize provider activity data into the existing completed workout domain.
- Normalize sleep/readiness/recovery signals into the recovery domain.
- Track connection status, last sync time, and sync failures per provider.
- Make re-sync idempotent using provider event/sample IDs.
- Define duplicate handling when Strava, Garmin, and Apple Health report the
  same workout.
- Define precedence for overlapping recovery data from Oura, Whoop, and Apple
  Health.

## Acceptance Criteria

- At least one provider connects in a non-production test environment.
- Initial sync and repeated sync do not create duplicate rows.
- Dashboard surfaces connection and sync status.
- Provider data can influence recovery or plan context without breaking users
  who only connect Strava.
