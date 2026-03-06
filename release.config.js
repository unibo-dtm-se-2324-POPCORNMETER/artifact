let dryRun = (process.env.RELEASE_DRY_RUN || "false").toLowerCase() === "true";
let testPypi = (process.env.RELEASE_TEST_PYPI || "false").toLowerCase() === "true";
let pypiUsername = process.env.PYPI_USERNAME;
let pypiPassword = process.env.PYPI_PASSWORD;

if (!pypiUsername || !pypiPassword) {
    dryRun = true;
    console.warn("PYPI_USERNAME or PYPI_PASSWORD not set. Running in dry-run mode.");
}

let prepareCmd = "poetry version -- ${nextRelease.version}";
let publishCmd = "";
let publishBaseCmd = "poetry publish --build";

if (testPypi) {
    // test-pypi repository name is defined in poetry.toml
    publishBaseCmd = `${publishBaseCmd} --repository pypi-test`;
}

if (dryRun) {
    // In dry-run mode without PyPI creds, only build artifacts.
    if (!pypiUsername || !pypiPassword) {
        publishCmd = "poetry build";
    } else {
        publishCmd = `${publishBaseCmd} --dry-run --username ${pypiUsername} --password ${pypiPassword}`;
    }
} else {
    publishCmd = `${publishBaseCmd} --username ${pypiUsername} --password ${pypiPassword}`;
}

import config from 'semantic-release-preconfigured-conventional-commits' with {type: 'json'};

// Keep Git tags and package versions in the same numeric format (e.g., 1.2.3).
config.tagFormat = "${version}";
// Release only from main release branches.
config.branches = ["master", "main"];

config.plugins.push(
    ["@semantic-release/exec", {
        "prepareCmd" : prepareCmd,
        "publishCmd": publishCmd,
    }]
)

if (!dryRun) {
    config.plugins.push(
        ["@semantic-release/github", {
            "assets": [
                { "path": "dist/*" },
            ]
        }],
        ["@semantic-release/git", {
            "assets": [
                "CHANGELOG.md",
                "pyproject.toml"
            ],
            "message": "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}"
        }]
    );
}

export default config;
