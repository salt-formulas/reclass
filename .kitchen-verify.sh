#!/bin/bash
#set -x

# setup
source /*.env
INVENTORY_BASE_URI=/tmp/kitchen/test/model/$MODEL
RECLASS=/tmp/kitchen

# prereq
python -m ensurepip --default-pip
pip install pipenv

# env
cd $RECLASS
pipenv --venv || pipenv install --python ${PYVER}
test -e /etc/reclsss || mkdir /etc/reclass
cp -avf $INVENTORY_BASE_URI/reclass-config* /etc/reclass

# verify
for n in $(ls $INVENTORY_BASE_URI/nodes/*|sort); do
  pipenv run python${PYVER} ./reclass.py --inventory-base-uri=$INVENTORY_BASE_URI --nodeinfo $(basename $n .yml)
done
