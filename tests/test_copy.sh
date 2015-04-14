
cp -r tests/data/water/ /tmp/testdir

cd /tmp/testdir
gpy init

cd ..
gpy copy testdir testdir2

if [ -e 'testdir2' ]; then
    echo OK Create dir
else
    echo FAIL Create dir
fi

if [ -e 'testdir2/.gpy' ]; then
    echo OK .gpy
else
    echo FAIL .gpy
fi

rm -rf /tmp/testdir /tmp/testdir2
