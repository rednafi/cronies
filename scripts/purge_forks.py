from __future__ import annotations
import httpx
import os
import asyncio
import logging
from contextlib import AsyncExitStack

# Get the GitHub API token from the environment.
GITHUB_API_TOKEN = os.environ["GITHUB_API_TOKEN"]
GITHUB_USERNAME = os.environ["GITHUB_USERNAME"]

# Create an HTTP client.
http_client = httpx.AsyncClient()

# Configure basic logger.
logging.basicConfig(level=logging.INFO)


async def get_forked_repos(http_client: httpx.AsyncClient) -> list[str]:
    """Get a list of all forked repositories."""

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

        # Get the list of forked repositories.
        forked_repo_urls.extend(
            [repo["url"] for repo in response.json() if repo["fork"] is True]
        )

    # Return the list of repositories.
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

    # Get the list of forked repositories.
    forked_repo_urls = await get_forked_repos(http_client)

    # If there are no forked repositories, exit.
    if not forked_repo_urls:
        logging.info("No forked repositories found.")
        return

    async with AsyncExitStack() as stack:
        task_group = await stack.enter_async_context(asyncio.TaskGroup())
        await stack.enter_async_context(asyncio.Timeout(10))
        for repo_url in forked_repo_urls:
            task_group.create_task(delete_forked_repo(http_client, repo_url))


if __name__ == "__main__":
    asyncio.run(main())
