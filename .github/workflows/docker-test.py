name: Docker Tests

on:
  pull_request:
    types: [opened, synchronize]
  workflow_dispatch:

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  docker:
    name: Docker Linux
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # Run Docker Compose Action
      - uses: adambirds/docker-compose-action@v1.5.0
        with:
          compose-file: "./docker/docker-compose.example.yml"
          up-flags: "--build"
          down-flags: "--volumes"
