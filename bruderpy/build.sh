#!/bin/sh
echo docker run --rm --privileged -v ~/.docker:/root/.docker -v "$(dirname "$(readlink -f "$0")")":/data homeassistant/amd64-builder --all --test
