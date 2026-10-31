# Roadmap

## Github action - deploy prod

Build job, on GitHub's runners:

Deploy job, on the self-hosted runner, from the folder that holds compose.yaml and the production .env:

export DEVNET_IMAGE=ghcr.io/<org>/devnet DEVNET_TAG=<git sha>
docker compose pull worker
docker compose run --rm deploy prefect work-pool pause devnet

...wait until no flow run is Running...

docker compose up -d
docker compose run --rm deploy # prefect deploy --all, from the new image
docker compose run --rm deploy prefect work-pool resume devnet
Give the wait a timeout. A run killed by an earlier crash stays Running forever, and you'd clear it in the UI.

## TODO

https://carlmontanari.github.io/scrapli/examples/python/

https://github.com/networktocode/diffsync
