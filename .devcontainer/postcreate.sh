#!/bin/zsh

# Install dependencies
poetry install --with dev

# Auto set up remote when pushing new branches
git config --global --add push.autoSetupRemote 1

git config --global --add safe.directory /workspaces/django-resilient-webhook

# Install precommit hooks
pre-commit install && pre-commit install -t commit-msg
pre-commit install-hooks
