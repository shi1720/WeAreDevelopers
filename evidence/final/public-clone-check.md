# Public GitHub clone and post-export package check

Operator verification at 2026-09-27T18:27:40.805449+00:00. This is post-run publication evidence, separate from the BAND seats' preserved acceptance logs.

The repository is publicly accessible. An unauthenticated GitHub API request returned HTTP 200 with `private: false` and `visibility: public`. A fresh HTTPS clone succeeded with system/global Git configuration disabled, credential helpers cleared, prompting disabled and no askpass program. No account token or authorization header was supplied.

## Commands and results

The clone was created at `/Users/shivamgupta/.cache/proofline-github-public-twlsnccb/repo`. The executed Git process used the following environment overrides: `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_TERMINAL_PROMPT=0`. Inherited `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_*`, `GIT_CONFIG_VALUE_*`, `GIT_ASKPASS` and `SSH_ASKPASS` were removed.

```sh
GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_TERMINAL_PROMPT=0 \
  git -c credential.helper= -c core.askPass= clone \
  https://github.com/shi1720/WeAreDevelopers.git /Users/shivamgupta/.cache/proofline-github-public-twlsnccb/repo
git -C /Users/shivamgupta/.cache/proofline-github-public-twlsnccb/repo rev-parse HEAD
```

Clone exit: **0**. Exact cloned HEAD: `fb76fd0487212119f5b0fa7e6f7722057b93ddd7`, matching the published candidate.

The GitHub visibility check used Python `urllib.request` against `https://api.github.com/repos/shi1720/WeAreDevelopers`, supplying only an Accept header and a User-Agent. It did not use an authenticated GitHub CLI session. The response was limited to visibility facts in the saved evidence.

For each folder, `git -C <clone> rev-parse HEAD:stage-N` was compared with `git rev-parse fb76fd0487212119f5b0fa7e6f7722057b93ddd7:stage-N` in the original checkout:

| Folder | Matching Git tree |
|---|---|
| stage-1 | `93744383122e819f760d2bf0a95dddf6fc791e13` |
| stage-2 | `3cff1d59fd5dbf0a625e5b223ce222dc87fcd0f4` |
| stage-3 | `bc31c3a67f21957cc6b0fbf11e9455661d9df179` |
| stage-4 | `53912d0263085f441225f962351d8876fef68ca1` |

The cloned `room.json` SHA-256 is `5608a22b314bb25ddb46b8e1004581a3480c04f46bd3219f28483cf40eb22fbb`, exactly matching the audited official full-session download. It was computed with Python `hashlib.sha256(path.read_bytes()).hexdigest()`.

```sh
cd /tmp/proofline-official-spec
.venv/bin/python -m harness check /Users/shivamgupta/.cache/proofline-github-public-twlsnccb/repo --track tablekeeper
```

Official package check exit: **0**. Gates 1, 2 and the mandate portion of gate 4 pass. The complete checker response and comparison data are in [public-clone-check.txt](public-clone-check.txt).

This offline check does not run the service or establish hidden-test results. No container/service suites were repeated because the accepted stage trees are unchanged; the existing [final verification](verification.md) retains those measured results. Video completion, hosted companion validation and platform submission receipt remain separate deliverables.

The published FACTORY.md now consistently reports exact dispatch-to-final-report duration **6 hours, 24 minutes, 4.981519 seconds**, including recovery/idle time. The published `.gitattributes` marks PDF, PPTX and media as binary, avoiding spurious text/whitespace treatment. Historical coordinator timestamps and logs remain unchanged.

No Git commit, push, cloud mutation, BAND message or stage edit was performed for this verification. Only these two operator evidence files were added to the main checkout.
