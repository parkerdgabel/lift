# Release Guide

This document describes how to create a new release of LIFT with multi-platform distribution.

## Pre-Release Checklist

1. **Update Version Number**
   - Update version in `pyproject.toml`
   - Ensure version follows [Semantic Versioning](https://semver.org/)

2. **Update CHANGELOG.md**
   - Add a new section for the version with date
   - List all changes under appropriate categories (Added, Changed, Fixed, etc.)
   - Follow [Keep a Changelog](https://keepachangelog.com/) format

3. **Run Tests Locally**
   ```bash
   pytest
   ruff check lift
   ruff format --check lift
   ```

4. **Test Build Locally**
   ```bash
   python -m build
   pip install dist/lift-*.whl  # Test installation
   lift version  # Verify it works
   ```

5. **Commit All Changes**
   ```bash
   git add -A
   git commit -m "Prepare release vX.Y.Z"
   git push origin main
   ```

## Creating a Release

### 1. Create and Push a Git Tag

```bash
# Create an annotated tag
git tag -a v0.1.0 -m "Release version 0.1.0"

# Push the tag to GitHub
git push origin v0.1.0
```

### 2. Automated Build Process

Once the tag is pushed, GitHub Actions will automatically:

1. **Build Python Package** (`build-python` job)
   - Run tests
   - Build wheel and source distribution
   - Calculate SHA256 checksums
   - Upload to artifacts

2. **Build Homebrew Formula** (`build-homebrew` job)
   - Generate Homebrew formula with correct SHA256
   - Test formula syntax
   - Upload formula to artifacts

3. **Build Debian Package** (`build-debian` job)
   - Build .deb package
   - Generate .buildinfo and .changes files
   - Upload to artifacts

4. **Create GitHub Release** (`release` job)
   - Collect all artifacts
   - Extract release notes from CHANGELOG.md
   - Create GitHub release with all packages attached

5. **Publish to PyPI** (`publish-pypi` job)
   - Publish wheel and source distribution to PyPI
   - Uses trusted publishing (no API token needed)

## Distribution Channels

### PyPI (Python Package Index)

Automatically published when a tag is pushed.

**Installation:**
```bash
pip install lift
```

**Requirements:**
- PyPI trusted publishing must be configured in repository settings
- Environment named `pypi` must exist in GitHub repository settings

### Homebrew (macOS/Linux)

The Homebrew formula (`lift.rb`) is included in the GitHub release.

**Manual Installation:**
```bash
# Download the formula from the release
curl -O https://github.com/parkerdgabel/lift/releases/download/v0.1.0/lift.rb

# Install using the formula
brew install ./lift.rb
```

**Optional: Homebrew Tap**
To enable automatic updates via a tap repository:

1. Create a tap repository: `https://github.com/parkerdgabel/homebrew-lift`
2. Add the formula to `Formula/lift.rb`
3. Enable the `update-homebrew-tap` job in `.github/workflows/release.yml`
4. Add `HOMEBREW_TAP_TOKEN` to repository secrets

Users can then install via:
```bash
brew tap parkerdgabel/lift
brew install lift
```

### Debian/Ubuntu (APT)

The .deb package is included in the GitHub release.

**Manual Installation:**
```bash
# Download the .deb package
wget https://github.com/parkerdgabel/lift/releases/download/v0.1.0/lift_0.1.0-1_all.deb

# Install the package
sudo dpkg -i lift_0.1.0-1_all.deb

# Install dependencies if needed
sudo apt-get install -f
```

**Optional: Custom APT Repository**
For automatic updates via apt, you can set up a custom repository using:
- GitHub Pages + aptly
- Gemfury
- Cloudsmith
- Self-hosted repository

## Post-Release Tasks

1. **Verify PyPI Publication**
   - Check https://pypi.org/project/lift/
   - Test installation: `pip install lift==X.Y.Z`

2. **Verify GitHub Release**
   - Check https://github.com/parkerdgabel/lift/releases
   - Verify all artifacts are attached
   - Review release notes

3. **Test Installations**
   ```bash
   # Test PyPI
   pip install lift==X.Y.Z
   lift version

   # Test Homebrew formula
   brew install ./lift.rb
   lift version

   # Test Debian package
   sudo dpkg -i lift_X.Y.Z-1_all.deb
   lift version
   ```

4. **Announce the Release**
   - Update project README if needed
   - Post on relevant forums/communities
   - Update documentation

## Troubleshooting

### PyPI Publishing Fails

**Error: "Trusted publishing exchange failure"**
- Ensure PyPI trusted publishing is configured
- Verify the `pypi` environment exists in GitHub settings
- Check that the workflow has correct permissions

### Debian Build Fails

**Error: "Cannot find dependencies"**
- Debian dependencies may not be available in Ubuntu repositories
- Consider using `pip` to install Python dependencies in the package
- See `debian/rules` for custom installation logic

### Homebrew Formula Invalid

**Error: "Invalid formula"**
- Verify SHA256 checksum matches the tarball
- Test formula locally: `brew install --build-from-source ./lift.rb`
- Check formula syntax: `brew audit --strict lift.rb`

## Version Numbering

LIFT follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version (X.0.0): Incompatible API changes
- **MINOR** version (0.X.0): New functionality, backwards compatible
- **PATCH** version (0.0.X): Bug fixes, backwards compatible

Examples:
- `0.1.0` - Initial release
- `0.2.0` - New features added
- `0.2.1` - Bug fixes
- `1.0.0` - Stable API, production ready

## Rolling Back a Release

If you need to remove a release:

1. **Delete the Git Tag**
   ```bash
   git tag -d v0.1.0
   git push origin :refs/tags/v0.1.0
   ```

2. **Delete GitHub Release**
   - Go to Releases page
   - Click "Delete" on the release

3. **Yank from PyPI** (if published)
   ```bash
   # PyPI doesn't allow deletion, but you can "yank" it
   # This requires PyPI credentials
   ```

## Release Checklist Template

```markdown
- [ ] Version bumped in pyproject.toml
- [ ] CHANGELOG.md updated with changes
- [ ] Tests passing locally
- [ ] Build successful locally
- [ ] Changes committed and pushed
- [ ] Git tag created and pushed
- [ ] GitHub Actions workflow completed successfully
- [ ] GitHub release created with all artifacts
- [ ] PyPI package published
- [ ] Homebrew formula available
- [ ] Debian package available
- [ ] Installation tested on all platforms
- [ ] Release announced
```
