#!/bin/bash

set -x

# load env
source /*.env

# upload model
rsync -avh --force /tmp/kitchen/test/model/$MODEL /etc/reclass
#cp -av /tmp/kitchen/test/model/$MODEL /etc/reclass

# test nodes
for n in $(ls /etc/reclass/nodes/*); do
  $PYVER ./reclass.py --nodeinfo $n
done
