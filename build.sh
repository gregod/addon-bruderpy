#!/bin/sh
docker run \
	--rm \
	--privileged \
	-v ~/.docker:/root/.docker \
	-v /var/run/docker.sock:/var/run/docker.sock:ro \
	-v "$(dirname "$(readlink -f "$0")")":/data \
	homeassistant/amd64-builder \
		--all \
		-t /data
