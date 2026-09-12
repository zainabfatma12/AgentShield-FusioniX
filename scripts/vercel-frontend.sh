#!/bin/sh
set -e

if [ -f package.json ] && [ -f vite.config.js ]; then
  APP="."
elif [ -f frontend/package.json ]; then
  APP="frontend"
elif [ -f ../frontend/package.json ]; then
  APP="../frontend"
else
  echo "Could not find frontend/package.json from $(pwd)" >&2
  exit 1
fi

echo "Using frontend at $APP (cwd=$(pwd))"
npm install --prefix "$APP"
npm run build --prefix "$APP"

if [ "$APP" != "." ]; then
  rm -rf dist
  cp -R "$APP/dist" dist
fi
