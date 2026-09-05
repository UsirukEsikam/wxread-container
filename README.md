# wxread-container

A thin container packaging layer for `findmover/wxread`.

## Design

- Do not fork or patch upstream application code.
- GitHub Actions checks out the latest upstream `main` branch and builds a Linux ARM64 image.
- Supercronic runs inside the container and schedules `runner.py`.
- `runner.py` runs upstream `main.py` unchanged and adds Bark notifications based on the process result.
- Runtime secrets stay on the deployment host.
- A wrapper timeout prevents an upstream network request from leaving the daily job stuck indefinitely.

## GitHub setup

1. Create a repository, for example `wxread-container`.
2. Add these files and push to `main`.
3. Run **Actions -> Build image -> Run workflow** once.
4. The image is published as:
   - `ghcr.io/<owner>/<repo>:latest`
   - `ghcr.io/<owner>/<repo>:upstream-<sha>`

The scheduled workflow runs once per day and always checks out the current upstream `main` branch. Packaging changes and manual workflow runs also build an image.

The upstream repository currently has no visible license file. For personal use, keeping the GHCR package private is the conservative default.

## Mac mini deployment

1. Copy `wxread.env.example` to `wxread.env`.
2. Set `WXREAD_CURL_BASH` and, if wanted, `BARK_KEY`.
3. Restrict access to the local secret file:

       chmod 600 wxread.env

4. Replace `YOUR_GITHUB_USER` in `compose.yaml` with the actual GHCR owner. If the repository name is not `wxread-container`, change that too.
5. If the GHCR package is private, log in with a GitHub token that can read packages.
6. Start:

       docker compose pull
       docker compose up -d

7. Run once manually for verification:

       docker compose exec wxread python /app/runner.py

8. Follow logs:

       docker compose logs -f wxread

The Compose file uses raw `env_file` parsing, which requires Docker Compose 2.30.0 or newer. This preserves `$`, quotes, and similar characters inside `WXREAD_CURL_BASH`.

## Runtime behavior

The default schedule is `0 1 * * *` in `Asia/Shanghai`. Change `CRON_SCHEDULE` or `TZ` in `wxread.env` if needed, then recreate the container:

    docker compose up -d --force-recreate

`WXREAD_CURL_BASH` is required. Bark is optional. If the upstream job exits with an error or exceeds its safety timeout, `runner.py` reports failure to Bark when Bark is configured and preserves a non-zero process result for manual runs.

Container output goes to Docker logs. The Compose file limits the local JSON logs to three 10 MB files; no application log volume is required.
