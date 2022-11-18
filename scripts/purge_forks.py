"""
To test the script locally, perform the following steps:

* Create a Python 3.11+ virtual environment.
* Install the dependencies.
* Export the following environment variables:
    * GITHUB_USERNAME
    * GITHUB_API_TOKEN
    * TIMEOUT
* Run the script:
    ```
    python -m scripts.purge_forks
    ```
"""

from __future__ import annotations
import httpx
import os
import asyncio
import logging
from contextlib import AsyncExitStack
import datetime


# Get the GitHub API token from the environment.
GITHUB_API_TOKEN = os.environ.get("GITHUB_API_TOKEN")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")

# The script will raise an exception if the timeout is reached.
TIMEOUT = float(timeout) if (timeout := os.environ.get("TIMEOUT")) else None

# Only delete forks that haven't been updated in the last 60 days.
OLDER_THAN = int(older_than) if (older_than := os.environ.get("OLDER_THAN")) else 60

# Raise runtime error if any of the environment variables are missing.
if all(
    None is env_var
    for env_var in (GITHUB_API_TOKEN, GITHUB_USERNAME, TIMEOUT, OLDER_THAN)
):
    raise RuntimeError(
        "Missing environment variables. Please set 'GITHUB_API_TOKEN', 'GITHUB_USERNAME', 'TIMEOUT', and 'OLDER_THAN'.",
    )

# Configure basic logger.
logging.basicConfig(level=logging.INFO)


async def get_forked_repos(
    http_client: httpx.AsyncClient,
    older_than: int = OLDER_THAN,  # 60 days.
) -> list[str]:
    """Get a list of all forked repositories.

    Args:
        http_client (httpx.AsyncClient): HTTP client.
        older_than (int): Only collect repos that are forked before 'older_than' days.
    """

    logging.info("Getting the list of forked repositories...")
    # Get the list of repositories.
    response = await http_client.head(
        f"https://api.github.com/users/{GITHUB_USERNAME}/repos",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GITHUB_API_TOKEN}",
        },
    )
    # Raise an exception if the request failed.
    response.raise_for_status()

    # Get the number of paginated urls.
    num_pages = int(
        response.headers["link"]
        .split(",")[-1]
        .split(";")[0]
        .split("=")[-1]
        .replace(">", "")
    )

    forked_repo_urls = []
    for current_page in range(1, num_pages + 1):
        # Get the list of repositories.
        response = await http_client.get(
            f"https://api.github.com/users/{GITHUB_USERNAME}/repos?page={current_page}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {GITHUB_API_TOKEN}",
            },
        )
        # Raise an exception if the request failed.
        response.raise_for_status()

        # Get current UTC datetime.
        current_dt = datetime.datetime.now(datetime.UTC)

        # 60 days ago.
        older_than_dt = current_dt - datetime.timedelta(days=older_than)

        for repo in response.json():
            if not repo["fork"]:
                continue

            # Get the datetime when the repo was forked.
            last_updated_dt = datetime.datetime.strptime(
                repo["updated_at"], "%Y-%m-%dT%H:%M:%SZ"
            )

            # Add tzinfo to the datetime.
            last_updated_dt = last_updated_dt.replace(tzinfo=datetime.UTC)

            # If the forked repo was last updated before 60 days, add it to the list.
            if last_updated_dt < older_than_dt:
                forked_repo_urls.append(repo["url"])

    # Return the list of forked repositories.
    return forked_repo_urls


async def delete_forked_repo(http_client: httpx.AsyncClient, repo_url: str) -> None:
    """Delete a forked repository."""

    # Delete the repository.
    response = await http_client.delete(
        repo_url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GITHUB_API_TOKEN}",
        },
    )
    # Raise an exception if the request failed.
    response.raise_for_status()
    logging.info(f"Deleted '{repo_url}'.")


async def main() -> None:
    """Main function."""

    # Create an HTTP client.
    http_client = httpx.AsyncClient()

    # Get the list of forked repositories.
    forked_repo_urls = await get_forked_repos(http_client)

    # If there are no forked repositories that were updated more than 60 days ago, exit.
    if not forked_repo_urls:
        logging.info(
            "No forked repositories found that were updated more than %s days ago.",
            OLDER_THAN,
        )
        return

    async with AsyncExitStack() as stack:
        await stack.enter_async_context(asyncio.timeout(TIMEOUT))
        task_group = await stack.enter_async_context(asyncio.TaskGroup())

        logging.info("Deleting forked repositories...")
        for repo_url in forked_repo_urls:
            task_group.create_task(delete_forked_repo(http_client, repo_url))


if __name__ == "__main__":
    asyncio.run(main())
