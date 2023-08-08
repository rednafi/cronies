# Cronies

Runs bespoke cron jobs.

## Description

* [fork-purger]: Purge forks that weren't updated in the last 60 days. Runs daily.

## Local development

To test the scripts locally:

* Make sure you have Go 1.21+ installed on your system.
* Head over to the root directory.
* Install the dependencies:
    ```sh
    go get
    ```
* Set the environment variables. This will vary depending on which script you're trying
to execute locally. See the instructions at the beginning of the individual scripts.
* Let's say, you want to run the [fork-purger] script. To do so, execute:
    ```sh
    go run scripts/fork_purger.go
    ```

[fork-purger]: .github/workflows/fork-purger.yml
