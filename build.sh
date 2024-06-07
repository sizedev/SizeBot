echo ------------BEGIN-------------;
branch=$1
botname=$2
botservice=${botname}
apiservice=${botname}api
dest=~/envs/${branch}

export PIPENV_YES=1;

echo =============STOP=============;
systemctl --user stop ${apiservice};
systemctl --user stop ${botservice};

echo ============BUILD=============;
rm -rf "${dest}";
mkdir "${dest}";
cd "${dest}" &&
~/.local/bin/pipenv --rm &&
git clone --depth=1 -b ${branch} https://github.com/sizedev/SizeBot.git . &&
~/.local/bin/pipenv install . &&
~/.local/bin/pipenv run pip install cysystemd &&
~/.local/bin/pipenv run pip install uwsgi &&
systemctl --user start ${botservice} &&
systemctl --user start ${apiservice};
code=$?;\

echo ============STATUS============;
systemctl --user status ${botservice};
systemctl --user status ${apiservice};

echo =============LOG==============;
journalctl --user -u ${botservice} --since "$(systemctl show -p InactiveExitTimestamp --value --user ${botservice})";\

echo -------------END--------------;
exit $code;
