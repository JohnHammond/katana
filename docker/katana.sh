#!/usr/bin/env bash
# Check for katana updates and then run Katana

function failure
{
	echo "[!] error: $*"
	exit 1
}

function update_katana
{

	# Prompt if user wants to update
	declare -- ANSWER=;
	until [[ $ANSWER =~ [yYnN] ]]; do
		read -rp "[?] update katana (y/n): " ANSWER
	done

	if ! [[ $ANSWER =~ [yY] ]]; then
		echo "[*] skipping update"
		return
	fi

	echo "[+] installing katana upgrades"

	# Grab new changes
	git pull || failure "git pull failed"

	# Run pip installer just in case
	pip install -r requirements.txt || failure "pip install failed"
}

# Ensure we are in the repo
cd /katana

# Check for updates to current branch
echo "[+] checking for updates"

git remote update >/dev/null
if git status -uno | grep "branch is up to date with" >/dev/null; then
	echo "[+] katana is up to date!"
else
	echo "[*] newer katana version avaiable (you should rebuild your docker)"
	update_katana
fi

# Run katana
python -m katana "$@"
