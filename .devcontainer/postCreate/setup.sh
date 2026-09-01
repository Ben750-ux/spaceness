#!/bin/bash
set -e
echo "=== Setup projet Spaceness (React Native / Expo) ==="
echo "Node: $(node -v)"
echo "npm: $(npm -v)"

# Installe les dependances de l'app mobile (le projet Expo est dans mobile/)
if [ -f "mobile/package.json" ]; then
  echo "=== Installation des dependances Expo (mobile/) ==="
  (cd mobile && npm install)
else
  echo "OK: mobile/package.json introuvable, deps deja presentes."
fi

# Verifie que la CLI Expo locale est disponible
(cd mobile && npx expo --version)
echo "=== Setup termine. Lancer avec: cd mobile && npx expo start --tunnel ==="
