# Keystroke Biometrics

Identify users by typing patterns (keyboard dynamics). Modern web UI, lightweight ML backend, local YAML storage.

## Quick start


## Features
- Real-time capture and visualization (dwell, flight, latency, speed, rhythm)
- Random Forest + multi-metric similarity (Euclidean, Manhattan, Cosine, timing)
- User profiles: multiple samples averaged; details modal with variation stats
- Registered users panel; YAML persistence with JSON backup/migration

## API
- GET  — status
- POST  — { username, text, keystroke_events }
- POST  — top similar users
- GET  — list users
- GET  — details/averages
- GET  — totals/averages

## Privacy
All data stays local under  (git-ignored).

## License
MIT
