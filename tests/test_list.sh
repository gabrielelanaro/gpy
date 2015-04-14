###########
# Test 1
###########
echo '---------- TEST 1 ----------'
echo 'Creating test structure'

mkdir -p /tmp/testdir/calc1/calc1.1
mkdir -p /tmp/testdir/calc2
cd /tmp/testdir/
gpy init
gpy init calc1
gpy init calc2
gpy init calc1/calc1.1

gpy list
echo 'Deleting test directory'
rm -rf /tmp/testdir/
