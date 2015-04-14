#!/bin/bash

###########
# Test 1
###########
echo '---------- TEST 1 ----------'
echo 'Creating test directory'
mkdir /tmp/testdir/

cd /tmp/testdir/

echo 'Testing init'
gpy init

if [ -e '.gpy' ]; then
    echo OK .gpy
else
    echo FAIL .gpy
fi

echo 'Deleting test directory'
rm -rf /tmp/testdir/

cd /tmp

###########
# Test 2
###########
echo '---------- TEST 2 ----------'

echo 'Creating test directory'
mkdir /tmp/testdir/

echo 'Testing init with path'
gpy init testdir

if [ -e 'testdir/.gpy' ]; then
    echo OK .gpy
else
    echo FAIL .gpy
fi

echo 'Deleting test directory'
rm -rf /tmp/testdir/
