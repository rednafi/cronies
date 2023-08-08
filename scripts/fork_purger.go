/*
Script to delete all forked repos older than 60 days. To test it locally:

- Ensure you have go 1.21+ installed
- Install the dependencies with `go get ./scripts/...`
- The following env vars are set:
	- GH_TOKEN: a personal access token with repo delete access
	- GH_USERNAME: the username of the account to delete forked repos from
- Run `go run scripts/fork_purger.go`
*/

package main

import (
	"context"
	"log"
	"os"
	"time"

	"github.com/google/go-github/v53/github"
	"golang.org/x/oauth2"
)

const (
	timeout   = 1 * time.Second
	olderThan = 24 * 60 * time.Hour
	perPage   = 100
)

var (
	githubAPIToken = os.Getenv("GH_TOKEN")
	githubUsername = os.Getenv("GH_USERNAME")
)

func init() {
	// Validate required env vars
	if githubAPIToken == "" || githubUsername == "" {
		log.Fatal("GH_TOKEN and GH_USERNAME must be set")
	}
}

func main() {
	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	// Authenticate client
	client := auth(ctx, githubAPIToken)

	// Get forked repos older than threshold
	repos, err := getForkedRepos(ctx, client, githubUsername, olderThan)
	if err != nil {
		log.Fatalf("could not get forked repos: %v", err)
	}

	// Log if no repos to delete
	if len(repos) == 0 {
		log.Println("no forked repos to delete")
		return
	}

	// Delete identified repos
	if err := deleteForkedRepos(ctx, client, repos); err != nil {
		log.Fatalf("could not delete repos: %v", err)
	}

	// Log results
	log.Printf(
		"deleted %d forked repos that are older than %d\n",
		len(repos), olderThan/(24*time.Hour),
	)
}

// auth creates an authenticated client
func auth(ctx context.Context, token string) *github.Client {
	ts := oauth2.StaticTokenSource(
		&oauth2.Token{AccessToken: token},
	)
	tc := oauth2.NewClient(ctx, ts)
	return github.NewClient(tc)
}

// getForkedRepos returns all forked repos older than the given threshold
func getForkedRepos(
	ctx context.Context,
	client *github.Client,
	username string,
	olderThan time.Duration,
) ([]*github.Repository, error) {

	opt := &github.RepositoryListOptions{
		ListOptions: github.ListOptions{
			PerPage: perPage,
		},
	}

	var repos []*github.Repository

	for {
		results, resp, err := client.Repositories.List(ctx, username, opt)

		if err != nil {
			return nil, err
		}

		for _, repo := range results {
			if *repo.Fork && time.Since(repo.CreatedAt.Time) > olderThan {
				repos = append(repos, repo)
			}
		}

		if resp.NextPage == 0 {
			break
		}
		opt.Page = resp.NextPage
	}
	return repos, nil
}

// deleteForkedRepos deletes the given repos
func deleteForkedRepos(
	ctx context.Context, client *github.Client, repos []*github.Repository) error {

	for _, repo := range repos {
		_, err := client.Repositories.Delete(ctx, *repo.Owner.Login, *repo.Name)
		if err != nil {
			return err
		}
	}
	return nil
}
