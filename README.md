# US Consumer Policy Archive

The store says you had 14 days to return the headphones. You remember seeing 30 when you bought them. What did the page actually say that week?

This small Python tool stores dated observations of public-facing US consumer policies. Look up the latest wording captured on or before a purchase or signup time, or compare it with the previous capture. Each result includes the observation timestamp and source URL.

## Try a return or cancellation lookup

Requires Python 3.10 or later. Uses the standard library only.

```sh
python3 archive.py demo
python3 archive.py lookup demo-returns --at 2026-11-05T18:00:00-05:00
python3 archive.py diff demo-returns --at 2026-11-10T18:00:00-05:00
python3 archive.py diff demo-cancellation --at 2026-11-10T18:00:00-05:00
```

The first lookup shows a 30-day return window. The first comparison shows it changing to 14 days. The cancellation example shows a change to a 48-hour cutoff. Both businesses and all sample clauses are fictional.

## Add a real observation

Copy the exact wording from a public policy page into a UTF-8 text file. Use a distinct policy key for each business, policy, and region or plan if the wording varies. Replace the example URL below with the page you observed.

```sh
python3 archive.py capture retailer-us-returns clause.txt --url https://example.org/returns
```

The capture uses the current time. For an existing dated observation, supply its original timestamp with `--at`. Run the same command with the same policy key when you next observe the page. Records are stored in a local SQLite file. Run `python3 -m unittest -v` to test the project.

## Reading a result

Every timestamp identifies an observation. A source page can change between captures. The archive does not establish an effective date or determine which terms govern an individual transaction. When a lookup predates the first capture, it reports the gap. The initial release supports manual captures and contains fictional demo data only.
