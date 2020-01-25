#!/bin/bash
# init
version=`python -c "import sys;t='{v[0]}.{v[1]}'.format(v=list(sys.version_info[:2]));sys.stdout.write(t)";`
if (( $(echo "$version < 3.7" | bc -l) )); then
   echo "The system detected Python ${version}. You need Python version 3.7 or above to run Sizebot. Exiting..."
   exit 1
fi
   echo 'Starting SizeBot'
   python -m sizebot
   read -n 1 -p 'Sizebot process has closed. Press any key to exit'
   exit 1