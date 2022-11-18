# cronies

Bespoke cron jobs.

## Description

* [`fork-purger`][1]: Purge forks that weren't updated in the last 60 days. Runs daily.

## Local development

To test the scripts locally:

* Create a Python 3.11+ environemnt:
    ```
    python -m venv .venv
    ```
* Activate the environment and install the dependencies:
    ```
    source .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt
    ```
* Set the environment variables. This will vary depending on which script you're trying
to execute locally. See the instructions in the individual scripts.
* Run a cron script locally:
    ```
    python -m scripts.<script_name>
    ```

[1]: ./github/workflows/fork-purger.yml
