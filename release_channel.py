"""Build-channel identity. Stable is the safe default for source/release builds.

Only the isolated GitHub Actions unstable preview workflow replaces this file
*in its ephemeral workspace* with CHANNEL='unstable' before packaging. Thus
normal stable releases can never accidentally be labelled as preview builds.
"""

CHANNEL = 'stable'
