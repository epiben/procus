#!/bin/zsh
echo "=== black ==="
black app/

echo "=== flake8 ==="
flake8 app/

echo "=== isort ==="
isort app/
