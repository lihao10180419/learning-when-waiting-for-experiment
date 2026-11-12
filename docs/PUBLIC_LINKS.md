# Public listing link verification

Checked on 12 November 2026 after the owner-authorized repository visibility change. GitHub returned `visibility: public` and `has_issues: true`.

Each exact HTTPS destination below was fetched using Python's standard-library HTTP client with **no Authorization header, login, Cookie or Git credential**. Redirects were followed; each returned HTTP 200 at the same URL. The rendered HTML body, with script/style payloads removed, was inspected for the expected plugin content. This checks public content, not merely an HTTP status. GitHub's public Issues page was also reachable.

| Listing field | Verified destination | Content checked |
| --- | --- | --- |
| websiteURL | [Plugin repository](https://github.com/lihao10180419/learning-when-waiting-for-experiment) | Plugin purpose, experiment waits, separate learning conversation, publisher handle |
| supportURL | [Support](https://github.com/lihao10180419/learning-when-waiting-for-experiment/blob/main/plugins/experiment-learning/docs/SUPPORT.md) | Installation/bug/privacy help instructions and GitHub Issues contact |
| privacyPolicyURL | [Privacy](https://github.com/lihao10180419/learning-when-waiting-for-experiment/blob/main/plugins/experiment-learning/docs/PRIVACY.md) | Local data categories, recipients, no automatic retention limit and user controls |
| termsOfServiceURL | [Terms](https://github.com/lihao10180419/learning-when-waiting-for-experiment/blob/main/plugins/experiment-learning/docs/TERMS.md) | Correct plugin/publisher, MIT license and no plugin fee/payment/purchase flow |

All four exact URLs are written into both manifests. Reading these pages requires no login; posting a support issue requires a GitHub account. This check is separate from the successful native acceptance in VERIFICATION.md and the documented route in ELIGIBILITY.md; OpenAI identity verification and review remain Portal steps. Recheck the links if hosting, visibility or paths change.
