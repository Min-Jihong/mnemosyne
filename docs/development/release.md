# Release Process

How to release a new version of Mnemosyne.

## Version Scheme

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

## Release Steps

### 1. Update Version

Update version in `pyproject.toml`:

```toml
[project]
version = "0.2.0"
```

### 2. Update Changelog

Add release notes to `CHANGELOG.md`:

```markdown
## [0.2.0] - 2024-XX-XX

### Added
- New feature X

### Changed
- Improved Y

### Fixed
- Bug Z
```

### 3. Create Release Commit

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v0.2.0"
```

### 4. Tag Release

```bash
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin main --tags
```

### 5. GitHub Release

1. Go to [Releases](https://github.com/yourusername/mnemosyne/releases)
2. Click "Draft a new release"
3. Select the tag
4. Copy changelog entry to description
5. Publish

### 6. PyPI (Automated)

The CI workflow automatically publishes to PyPI on tag push.

## Manual PyPI Release

If needed:

```bash
# Build
python -m build

# Test upload
twine upload --repository testpypi dist/*

# Production upload
twine upload dist/*
```

## Pre-release Versions

For pre-releases:

```
0.2.0-alpha.1
0.2.0-beta.1
0.2.0-rc.1
```

## Hotfix Process

1. Create hotfix branch from tag
2. Fix issue
3. Bump patch version
4. Release as above
