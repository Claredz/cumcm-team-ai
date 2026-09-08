#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
xelatex -interaction=nonstopmode -halt-on-error fig.tex
if grep -q "Missing character" fig.log; then
  echo "Missing character detected; fix fonts before use." >&2
  exit 2
fi
if command -v pdftoppm >/dev/null 2>&1; then
  pdftoppm -png -r 300 -singlefile fig.pdf fig
fi
if command -v pdftocairo >/dev/null 2>&1; then
  pdftocairo -svg fig.pdf fig.svg
fi
