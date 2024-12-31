---
title: CentOS
category: Installing the bot
order: 8
---
<img class="os-icon" src="{{ site.baseurl }}/images/centos.png" alt="CentOS logo"/>
Installation on CentOS is possible, however **support is no longer provided for any version of CentOS**.  
CentOS is considered End-of-Life, and so packages and repositories used in these steps may not exist today!  

CentOS Stream version 8 was included in the [Auto Installer]({{ site.baseurl }}/installing/installers) script. 
It may or may not work for you, please read the script before using it.  
If you are interested in installing on CentOS or other RHEL-like OS versions, please consider contributing up-to-date install steps for the OS of your choice.  

> **NOTICE:** These steps are provided for reference only. Carefully examine and update these steps to comply with your system. 

## CentOS 6.9

~~~sh
# Install dependencies
sudo yum -y update
sudo yum -y groupinstall "Development Tools"
sudo yum -y install https://centos6.iuscommunity.org/ius-release.rpm
sudo yum -y install gcc openssl-devel bzip2-devel libffi-devel make
sudo yum -y install yum-utils opus-devel libsodium-devel 

# Install Python3.10
cd /opt
wget https://www.python.org/ftp/python/3.10.13/Python-3.10.13.tgz
tar xzf Python-3.10.13.tgz
cd Python-3.10.13
sudo ./configure --enable-optimizations
sudo make altinstall
cd ..
sudo rm Python-3.10.13.tgz

# Install FFmpeg
sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro
sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el6/x86_64/nux-dextop-release-0-2.el6.nux.noarch.rpm
sudo yum -y install ffmpeg ffmpeg-devel -y

# Install libsodium from source
mkdir libsodium && cd libsodium
curl -o libsodium.tar.gz https://download.libsodium.org/libsodium/releases/LATEST.tar.gz
tar -zxvf libsodium.tar.gz && cd libsodium-stable
./configure
make && make check
sudo make install
cd ../.. && rm -rf libsodium

# Clone the MusicBot
git clone https://github.com/Just-Some-Bots/MusicBot.git MusicBot -b master
cd MusicBot

# Install bot requirements

python3 -m pip install -U -r requirements.txt
python3 -m pip install -U pynacl

~~~


## CentOS 7.4

~~~sh
# Install dependencies
sudo yum -y update
sudo yum -y groupinstall "Development Tools"
sudo yum -y install https://centos7.iuscommunity.org/ius-release.rpm
sudo yum -y install curl opus-devel libffi-devel libsodium-devel
sudo yum -y install gcc openssl-devel bzip2-devel make

# Install Python3.10

cd /opt
wget https://www.python.org/ftp/python/3.10.13/Python-3.10.13.tgz
tar xzf Python-3.10.13.tgz
cd Python-3.10.13
sudo ./configure --enable-optimizations
sudo make altinstall
cd ..
sudo rm Python-3.10.13.tgz

# Install FFmpeg
sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro
sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-5.el7.nux.noarch.rpm
sudo yum -y install ffmpeg ffmpeg-devel -y

# Clone the MusicBot
git clone https://github.com/Just-Some-Bots/MusicBot.git MusicBot -b review
cd MusicBot

# Install bot requirements

python3 -m pip install -U -r requirements.txt

~~~

## CentOS Stream 8

These are the steps used by the auto-installer script for CentOS Stream version 8.  

```bash

# Add extra repositories to system package manager.
sudo dnf install epel-release
sudo dnf install --nogpgcheck https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-8.noarch.rpm
sudo dnf config-manager --enable powertools

# Install available required packages.
sudo yum -y install opus-devel libffi-devel git curl jq ffmpeg python39 python39-devel

# Clone the MusicBot
git clone https://github.com/Just-Some-Bots/MusicBot.git MusicBot -b master
cd MusicBot

# Install bot requirements
python3 -m pip install -U -r requirements.txt

```

Once everything has been completed, you can go ahead and [configure]({{ site.baseurl }}/using/configuration) the bot and then run with `sudo ./run.sh`.
