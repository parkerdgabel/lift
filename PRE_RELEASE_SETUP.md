# Pre-Release Setup Checklist

Before creating your first release (v0.1.0), you need to configure PyPI trusted publishing. This is a one-time setup.

## 1. Create PyPI Account

1. Go to https://pypi.org/account/register/
2. Create an account and verify your email
3. Enable two-factor authentication (2FA) - **required for publishing**

## 2. Register the Package Name on PyPI

You need to create the project on PyPI before trusted publishing will work.

**Option A: Manual Registration**
1. Build the package locally:
   ```bash
   python -m pip install build
   python -m build
   ```

2. Upload to PyPI (one-time):
   ```bash
   pip install twine
   twine upload dist/*
   ```
   - Enter your PyPI username and password
   - This creates the `lift-tracker` project on PyPI

**Option B: Register via Web Interface**
1. Log in to https://pypi.org
2. Click "Your projects" → "Publishing"
3. Fill in the project name: `lift-tracker`

## 3. Configure PyPI Trusted Publishing

Trusted publishing allows GitHub Actions to publish to PyPI without API tokens.

1. **Go to PyPI Project Settings**
   - Navigate to https://pypi.org/manage/project/lift-tracker/settings/publishing/

2. **Add a New Trusted Publisher**
   - Click "Add a new pending publisher"
   - Fill in the form:
     - **PyPI Project Name:** `lift-tracker`
     - **Owner:** `parkerdgabel`
     - **Repository name:** `lift`
     - **Workflow name:** `release.yml`
     - **Environment name:** `pypi`

3. **Save the Configuration**

## 4. Configure GitHub Repository Settings

1. **Create PyPI Environment**
   - Go to https://github.com/parkerdgabel/lift/settings/environments
   - Click "New environment"
   - Name it exactly: `pypi`
   - No environment secrets needed (using trusted publishing)
   - Save

2. **Verify Repository Settings**
   - Go to https://github.com/parkerdgabel/lift/settings/actions
   - Under "Workflow permissions", ensure:
     - ✅ "Read and write permissions" is selected
     - ✅ "Allow GitHub Actions to create and approve pull requests" is checked

## 5. Test Build Locally (Optional but Recommended)

Before creating the release, test that everything builds correctly:

```bash
# Install build dependencies
pip install build

# Build the package
python -m build

# Check the built packages
ls -lh dist/

# Test installation locally
pip install dist/lift-*.whl
lift version
lift --help
```

## 6. Ready to Release!

Once the above steps are complete, you can create your first release:

```bash
# Create and push the v0.1.0 tag
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

GitHub Actions will automatically:
1. ✅ Run tests
2. ✅ Build Python package (wheel + source dist)
3. ✅ Build Homebrew formula
4. ✅ Build Debian package
5. ✅ Create GitHub release
6. ✅ Publish to PyPI (via trusted publishing)

## Verification

After pushing the tag, monitor the release process:

1. **GitHub Actions**
   - Watch: https://github.com/parkerdgabel/lift/actions
   - The "Release" workflow should start automatically

2. **GitHub Release**
   - Check: https://github.com/parkerdgabel/lift/releases
   - Should contain: wheel, sdist, .deb, and lift.rb

3. **PyPI**
   - Check: https://pypi.org/project/lift/
   - Should show version 0.1.0

## Troubleshooting

### "PyPI project not found"
- The project must exist on PyPI first
- Do Option A (manual upload) in step 2

### "Trusted publishing failed"
- Verify the environment name is exactly `pypi` (lowercase)
- Verify the workflow name is `release.yml`
- Check that the PyPI trusted publisher settings match exactly

### "Permission denied to create release"
- Check GitHub repository workflow permissions
- Ensure "Read and write permissions" is enabled

### "Debian build fails"
- This is expected if Debian dependencies aren't available
- The .deb package is optional
- Python package and Homebrew formula should still work

## Next Steps

After successful release:

1. ✅ Verify installation from PyPI: `pip install lift`
2. ✅ Test Homebrew formula installation
3. ✅ Share release announcement
4. ✅ Update project documentation if needed

For future releases, see [RELEASE.md](RELEASE.md) for the full release process.
