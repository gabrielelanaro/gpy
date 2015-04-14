
mkdir /tmp/testdata1/

cd /tmp/testdata1/

gpy init
mkdir templates
echo 'Run command for {hours} hours, on {cpus} CPUs, named {name}' > templates/qsub.tpl
echo 'Send also an email at {email}' >> templates/qsub.tpl

gpy qsub -n 64 -h 120

rm -rf /tmp/testdata1/
