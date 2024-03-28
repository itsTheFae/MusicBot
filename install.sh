#!/bin/bash
#
# MusicBot and this file are provided under an MIT license. 
# Please see the LICENSE file for details.
#
# This file attempts to provide automatic install of MusicBot and dependencies on
# a variety of different Linux distros.
# 

#----------------------------------------------Constants----------------------------------------------#
DEFAULT_URL_BASE="https://discordapp.com/api"
PYEXEC=3
DEBUG=0

USER_OBJ_KEYS="id username discriminator verified bot email avatar"

declare -A BOT

# Get some notion of the current OS / distro name.
# This will not exhaust options, or ensure a correct name is returned. 
if [ -n "$(command -v lsb_release)" ] ; then
    # Most debian-based distros will have this command.
    # Redhat-based distros usually need to install it via redhat-lsb-core package
    DISTRO_NAME=$(lsb_release -s -d)
elif [ -f "/etc/os-release" ]; then
    # Many distros have this file, but not all of them are version complete.
    # For example, CentOS 7 will return "CentOS Linux 7 (Core)"
    # If we need to know the minor version, we need /etc/redhat-release instead.
    DISTRO_NAME=$(grep PRETTY_NAME /etc/os-release | sed 's/PRETTY_NAME=//g' | tr -d '="')
elif [ -f "/etc/debian_version" ]; then
    DISTRO_NAME="Debian $(cat /etc/debian_version)"
elif [ -f "/etc/redhat-release" ]; then
    DISTRO_NAME=$(cat /etc/redhat-release)
else
    DISTRO_NAME="$(uname -s) $(uname -r)"
fi

#----------------------------------------------Functions----------------------------------------------#
function exit_err() {
    echo "$@"
    exit 1
}

function pull_musicbot_git() {
    cd ~ || exit_err "Fatal:  Could not change to home directory."
    echo " "
    echo "MusicBot currently has three branches available."
    echo "  master - An older MusicBot, for older discord.py. May not work without tweaks!"
    echo "  review - Newer MusicBot, usually stable with less updates than the dev branch."
    echo "  dev    - The newest MusicBot, latest features and changes which may need testing."
    echo ""
    read -rp "Enter the branch name you want to install:  " BRANCH
    case ${BRANCH,,} in
    "dev")
        echo "Installing from 'dev' branch..."
        git clone https://github.com/Just-Some-Bots/MusicBot.git MusicBot -b dev
        ;;
    "review")
        echo "Installing from 'review' branch..."
        git clone https://github.com/Just-Some-Bots/MusicBot.git MusicBot -b review
        ;;
    "master")
        echo "Installing from 'master' branch..."
        git clone https://github.com/Just-Some-Bots/MusicBot.git MusicBot -b master
        ;;
    *)
        exit_err "Unknown branch name given, install cannot continue."
        ;;
    esac
    cd MusicBot || exit_err "Fatal:  Could not change to MusicBot directory."

    python${PYEXEC} -m pip install --upgrade -r requirements.txt

    cp ./config/example_options.ini ./config/options.ini
}

function setup_as_service() {
    local DIR
    DIR="$(pwd)"
    echo ""
    echo "Do you want to set up the bot as a service?"
    read -rp "This would mean the bot is automatically started and kept up by the system to ensure its online as much as possible [N/y] " SERVICE
    case $SERVICE in
    [Yy]*)
        echo "Setting up the bot as a service"
        sed -i "s/versionnum/$PYEXEC/g" ./musicbot.service
        sed -i "s,mbdirectory,$DIR,g" ./musicbot.service
        sudo mv ~/MusicBot/musicbot.service /etc/systemd/system/
        sudo chown root:root /etc/systemd/system/musicbot.service
        sudo chmod 644 /etc/systemd/system/musicbot.service
        sudo systemctl enable musicbot
        sudo systemctl start musicbot
        echo "Bot setup as a service and started"
        ask_setup_aliases
        ;;
    esac

}

function ask_setup_aliases() {
    echo " "
    # TODO: ADD LINK TO WIKI
    read -rp "Would you like to set up a command to manage the service? [N/y] " SERVICE
    case $SERVICE in
    [Yy]*)
        echo "Setting up command..."
        sudo mv ~/MusicBot/musicbotcmd /usr/bin/musicbot
        sudo chown root:root /usr/bin/musicbot
        sudo chmod 644 /usr/bin/musicbot
        sudo chmod +x /usr/bin/musicbot
        echo ""
        echo "Command created!"
        echo "Information regarding how the bot can now be managed found by running:"
        echo "musicbot --help"
        ;;
    esac
}

function debug() {
    local msg=$1
    if [[ $DEBUG == '1' ]]; then
        echo "[DEBUG] $msg" 1>&2
    fi
}

function strip_dquote() {
    result="${1%\"}"
    result="${result#\"}"
    echo "$result"
}

function r_data() {
    local data=$1
    echo "$data" | sed -rn 's/(\{.+)\} ([0-9]+)$/\1}/p'
}

function r_code() {
    local data=$1
    echo "$data" | sed -rn 's/(\{.+)\} ([0-9]+)$/\2/p'
}

function key() {
    local data=$1
    local key=$2
    echo "$data" | jq ".$key"
}

function r() {
    local token=$1
    local method=$2
    local route=$3

    local url="$DEFAULT_URL_BASE/$route"
    debug "Attempting to load url $url with token $token"

    res=$(curl -k -s \
        -w " %{http_code}" \
        -H "Authorization: Bot $token" \
        -H "Content-Type: application/json" \
        -X "$method" \
        "$url" | tr -d '\n')
    echo "$res"
}

function get_token_and_create_bot() {
    # Set bot token
    echo ""
    echo "Please enter your bot token. This can be found in your discordapp developer page."
    read -rp "Enter Token:" -s token
    create_bot "$token"
}

function create_bot() {
    local bot_token=$1

    local me
    local me_code
    local me_data
    me=$(r "$bot_token" "GET" "users/@me")
    me_code=$(r_code "$me")
    me_data=$(r_data "$me")

    if ! [[ $me_code == "200" ]]; then
        echo ""
        echo "Error getting user profile, is the token correct? ($me_code $me_data)"
        exit 1
    else
        debug "Got user profile: $me_data"
    fi

    for k in $USER_OBJ_KEYS; do
        BOT[$k]=strip_dquote "$(key "$me_data" "$k")"
    done
    BOT["token"]=$bot_token

    # We're logged on!
    echo "Logged on with ${BOT["username"]}#${BOT["discriminator"]}"
    sed -i "s/bot_token/$bot_token/g" ./config/options.ini
}

function configure_bot() {
    read -rp "Would like to configure the bot for basic use? [N/y]" YesConfig
    if [ "${YesConfig,,}" != "y" ] && [ "${YesConfig,,}" != "yes" ] ; then
        return
    fi

    get_token_and_create_bot

    # Set prefix, if user wants
    read -rp "Would you like to change the command prefix? [N/y] " chngprefix
    case $chngprefix in
    [Yy]*)
        echo "Please enter the prefix you'd like for your bot."
        read -rp "This is what comes before all commands. The default is [!] " prefix
        sed -i "s/CommandPrefix = !/CommandPrefix = $prefix/g" ./config/options.ini
        ;;
    [Nn]*) echo "Using default prefix [!]" ;;
    *) echo "Using default prefix [!]" ;;
    esac

    # Set owner ID, if user wants
    read -rp "Would you like to automatically get the owner ID from the OAuth application? [Y/n] " accountcheck
    case $accountcheck in
    [Yy]*) echo "Getting owner ID from OAuth application..." ;;
    [Nn]*)
        read -rp "Please enter the owner ID. " ownerid
        sed -i "s/OwnerID = auto/OwnerID = $ownerid/g" ./config/options.ini
        ;;
    *) echo "Getting owner ID from OAuth application..." ;;
    esac
    # Enable/Disable AutoPlaylist
    read -rp "Would you like to enable the autoplaylist? [Y/n] " autoplaylist
    case $autoplaylist in
    [Yy]*) echo "Autoplaylist enabled." ;;
    [Nn]*)
        echo "Autoplaylist disabled"
        sed -i "s/UseAutoPlaylist = yes/UseAutoPlaylist = no/g" ./config/options.ini
        ;;
    *) echo "Autoplaylist enabled." ;;
    esac
}

#------------------------------------------------Logic------------------------------------------------#
# list off "supported" linux distro/versions if asked to and exit.
if [[ "${1,,}" == "--list" ]] ; then
    # We search this file and extract names from the supported cases below.
    # We control which cases we grab based on the space at the end of each 
    # case pattern, before ) or | characters.
    # This allows adding complex cases which will be excluded from the list.
    Avail=$(grep -oh '\*"[[:alnum:] _!\.]*"\*[|)]' "$0" )
    Avail="${Avail//\*\"/}"
    Avail="${Avail//\"\*/}"
    Avail="${Avail//[|)]/}"

    echo "The MusicBot installer might have support for these flavors of Linux:"
    echo "$Avail"
    echo ""
    exit 0
fi

cat << EOF
MusicBot Installer

MusicBot and this installer are provided under an MIT license.
This software is provided "as is" and may not be fit for any particular use, stated or otherwise.
Please read the LICENSE file for full details.

This installer attempts to provide automatic install for MusicBot and dependency packages.
It may use methods which are out-of-date on older OS versions, or fail on newer versions.
It is recommended that you personally check the installer script before running it,
and verify the steps for your OS and distro version are correct.

Please consider contributing corrections or new steps if you find issues with this installer.
You may also find installation guides on the wiki or community help on our discord server.
Wiki:
    https://just-some-bots.github.io/MusicBot/
Discord:
    https://discord.gg/bots

For a list of potentially supported OS, run the command:
  $0 --list


EOF

echo "We detected your OS is:  ${DISTRO_NAME}"

read -rp "Would you like to continue with the installer? [Y/n]:  " iagree
if [[ "${iagree,,}" != "y" && "${iagree,,}" != "yes" ]] ; then
    exit 2
fi

echo ""

case $DISTRO_NAME in
*"Arch Linux"*)
    sudo pacman -Syu
    sudo pacman -S git python python-pip opus libffi libsodium ncurses gdbm \
        glibc zlib sqlite tk openssl ffmpeg curl jq
    pull_musicbot_git
    ;;

*"Pop!_OS"*)
    sudo apt-get update -y
    sudo apt-get upgrade -y
    sudo apt-get install build-essential software-properties-common \
        unzip curl git ffmpeg libopus-dev libffi-dev libsodium-dev \
        python3-pip python3-dev jq -y

    pull_musicbot_git
    ;;

*"Ubuntu"* )
    case $DISTRO_NAME in
    # Using only major versions of Ubuntu to allow for both .04 and .10 minor versions.
    *"Ubuntu 18"*)
        PYEXEC="3.8"

        sudo apt-get update -y
        sudo apt-get upgrade -y
        # 18.04 needs explicit python3.8 package, and has no pip package.
        sudo apt-get install build-essential software-properties-common \
            unzip curl git ffmpeg libopus-dev libffi-dev libsodium-dev \
            python3.8-dev jq -y

        # python3.8 needs a manual pip install on 18.04
        python${PYEXEC} <(curl -s https://bootstrap.pypa.io/get-pip.py)

        pull_musicbot_git
        ;;
    *"Ubuntu 20"*|*"Ubuntu 22"*)
        sudo apt-get update -y
        sudo apt-get upgrade -y
        sudo apt-get install build-essential software-properties-common \
            unzip curl git ffmpeg libopus-dev libffi-dev libsodium-dev \
            python3-pip python3-dev jq -y

        pull_musicbot_git
        ;;
    *)
        echo "Unsupported version of Ubuntu."
        exit 1
        ;;
    esac
    ;;

*"Debian"*)
    sudo apt-get update -y
    sudo apt-get upgrade -y
    sudo apt-get install git libopus-dev libffi-dev libsodium-dev ffmpeg \
        build-essential libncursesw5-dev libgdbm-dev libc6-dev zlib1g-dev \
        libsqlite3-dev tk-dev libssl-dev openssl python3 python3-pip curl jq -y
    pull_musicbot_git
    ;;

# I don't know if this will still work.
# Raspberry Pi OS i386 (bullseye) does not return "Raspbian" you get "Debian" instead.
# I cannot test the arm versions without a board or an emulator...
# Guess it wont hurt to leave it in for now...
*"Raspbian"*)
    sudo apt-get update -y
    sudo apt-get upgrade -y
    sudo apt install python3-pip git libopus-dev ffmpeg curl
    curl -o jq.tar.gz https://github.com/stedolan/jq/releases/download/jq-1.5/jq-1.5.tar.gz
    tar -zxvf jq.tar.gz
    cd jq-1.5 || exit_err "Fatal:  Could not change directory to jq-1.5"
    ./configure && make && sudo make install
    cd .. && rm -rf ./jq-1.5
    pull_musicbot_git
    ;;

*"CentOS"* )
    # Get the full release name and version
    if [ -f "/etc/redhat-release" ]; then
        DISTRO_NAME=$(cat /etc/redhat-release)
    fi
    # Simplify the distro name for easier checking.
    DISTRO_NAME="${DISTRO_NAME//Linux /}"
    DISTRO_NAME="${DISTRO_NAME//release /}"

    case $DISTRO_NAME in
    # Handle the versions which are EOL.
    *"CentOS "[2-6]* |*"CentOS 8."[0-5]* )
        echo "Unfortunately, this version of CentOS has reached End-of-Life, and will not be supported."
        echo "You should consider upgrading to the latest version to make installing MusicBot easier."
        exit 1
        ;;

    # Supported versions.
    *"CentOS 7"*)
        # TODO:  CentOS 7 reaches EOL June 2024.

        # Enable extra repos, as required for ffmpeg
        # We DO NOT use the -y flag here.
        sudo yum install epel-release
        sudo yum localinstall --nogpgcheck https://download1.rpmfusion.org/free/el/rpmfusion-free-release-7.noarch.rpm

        # Install available packages and libraries for building python 3.8+
        sudo yum -y groupinstall "Development Tools"
        sudo yum -y install opus-devel libffi-devel openssl-devel bzip2-devel \
            git curl jq ffmpeg

        # Build python.
        PyBuildVer="3.10.14"
        PySrcDir="Python-${PyBuildVer}"
        PySrcFile="${PySrcDir}.tgz"

        curl -o "$PySrcFile" "https://www.python.org/ftp/python/${PyBuildVer}/${PySrcFile}"
        tar -xzf "$PySrcFile"
        cd "${PySrcDir}" || exit_err "Fatal:  Could not change to python source directory."

        ./configure --enable-optimizations
        sudo make altinstall

        pull_musicbot_git
        ;;

    *"CentOS Stream 8"*)
        # Install extra repos, needed for ffmpeg.
        # Do not use -y flag here.
        sudo dnf install epel-release
        sudo dnf install --nogpgcheck https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-8.noarch.rpm
        sudo dnf config-manager --enable powertools

        # Install available packages.
        sudo yum -y install opus-devel libffi-devel git curl jq ffmpeg python39 python39-devel

        pull_musicbot_git
        ;;

    # Currently unsupported.
    *)
        echo "This version of CentOS is not currently supported."
        exit 1
        ;;
    esac
    ;;

*"Darwin"*)
    /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    brew update
    xcode-select --install
    brew install python
    brew install git
    brew install ffmpeg
    brew install opus
    brew install libffi
    brew install libsodium
    brew install curl
    brew install jq
    pull_musicbot_git
    ;;

*)
    echo "Unsupported OS, you will have to install the bot manually."
    exit 1
    ;;
esac

if ! [[ $DISTRO_NAME == *"Darwin"* ]]; then
    configure_bot
    setup_as_service
else
    echo "The bot has been successfully installed to your user directory"
    echo "You can configure the bot by navigating to the config folder, and modifying the contents of the options.ini and permissions.ini files"
    echo "Once configured, you can start the bot by running the run.sh file"
fi
