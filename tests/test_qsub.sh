
mkdir /tmp/testdata1/

cd /tmp/testdata1/
gpy init

mkdir templates

echo 'Run command for {time} hours, on {cpus} CPUs, named {name}' > templates/qsub.tpl
echo 'Send also an email at {email}' >> templates/qsub.tpl


mkdir proj2
cd proj2
gpy init
gpy qsub --yes -c 64 -t 120 -n 'Job Name'
gpy qdel
rm -rf /tmp/testdata1/
