#!/bin/sh

# https://stackoverflow.com/questions/11147667/is-there-a-way-to-list-pip-dependencies-requirements
# https://gitlab.com/snippets/22979

PACKAGE=$1
pip download $PACKAGE -d /tmp --no-binary :all: \
| grep Collecting \
| cut -d' ' -f2 \
| grep -Ev "$PACKAGE(~|=|\!|>|<|$)"
