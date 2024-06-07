echo ------------BEGIN-------------;
branch=$1
if [ "$branch" -eq "master" ]; then
    botname="sizebot"
elif [ "$branch" -eq "develop" ]; then
    botname="nizebot"
else
    echo "Unrecognized branch: ${branch}";
    exit 1
fi
botservice=${botname}
apiservice=${botname}api
dest=~/envs/${branch}

echo =============STOP=============;
systemctl --user stop ${apiservice};
systemctl --user stop ${botservice};

echo ============BUILD=============;
rm -rf "${dest}";
mkdir "${dest}";
cd "${dest}" &&
git clone --depth=1 -b ${branch} https://github.com/sizedev/SizeBot.git . &&
rye sync --no-dev --features=linux &&
systemctl --user start ${botservice} &&
systemctl --user start ${apiservice};
code=$?;\

echo ============STATUS============;
systemctl --user status ${botservice};
systemctl --user status ${apiservice};

echo =============LOG==============;
journalctl --user -u ${botservice} --since "$(systemctl show -p InactiveExitTimestamp --value --user ${botservice})";

echo -------------END--------------;
exit $code;
