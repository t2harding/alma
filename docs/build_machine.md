# Setup

## Debian 9.3
Use the firmware-9.3 DVD ISO image [i386](https://cdimage.debian.org/cdimage/unofficial/non-free/cd-including-firmware/9.3.0+nonfree/i386/iso-dvd/firmware-9.3.0-i386-DVD-1.iso), [amd64](https://cdimage.debian.org/cdimage/unofficial/non-free/cd-including-firmware/9.3.0+nonfree/amd64/iso-dvd/firmware-9.3.0-amd64-DVD-1.iso)

### Software selection
Select
 * ... GNOME
 * ... LXDE
 * print server
 * SSH server
 * standard system utilites
 
### Configuring lightdm
For resource constrained installs select lightdm as the default display manager, otherwise select gdm3. (lightdm is fine for any machine)

### GRUB boot loader
Accept default to install GRUB boot loader to the master boot record.

## Setup after first boot
Log in as user with sudo permissions and install initial packages
`sudo apt-get install git build-essential cmake curl chromium libsecret-1-dev fakeroot rpm libx11-dev libxtst-dev libxkbfile-dev vim-gtk3 pkg-config ctags arduino python-pip tmux openocd binutils-arm-none-eabi gcc-arm-none-eabi gdb-arm-none-eabi libstdc++-arm-none-eabi-newlib`

## Add user to sudo list
Log in as root
`su -` Enter root passw
Add the user to the sudo group
`usermod -a -G sudo <username>`

## Setup with Tyson's defaults
`curl -Lks http://github.com/tharding/dotfiles/raw/master/.dotfiles/setup.sh | /bin/bash`

## Install Atom Editor on 32-bit machines
### Build the deb file
Install nvm
```
curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.8/install.sh | bash
. ~/.bashrc
nvm install --lts
nvm install-latest-npm
npm config set python /usr/bin/python -g
```
Download atom.io [source](https://github.com/atom/atom/archive/v1.23.1.tar.gz)
```
mkdir src
cd src
wget https://github.com/atom/atom/archive/v1.23.1.tar.gz
tar -xvzf v1.23.1.tar.gz
rm v1.23.1.tar.gz
cd atom-1.23.1
script/build --create-debian-package
sudo dpkg -i out/atom-i386.deb
```

### Install the deb file
```
scp tebor:/home/share/atom-i386.deb ./
sudo dpkg -i atom-i386.deb
rm atom-i386.deb
```

## Install Albert (application launcher)
Add repository for Albert and ksuperkey
```
wget -nv -O Release.key https://build.opensuse.org/projects/home:manuelschneid3r/public_key
sudo apt-key add - < Release.key
rm Release.key
sudo echo 'deb http://download.opensuse.org/repositories/home:/manuelschneid3r/Debian_9.0/ /' > /etc/apt/sources.list.d/albert.list
sudo apt-get update
sudo apt-get install albert
```

## Install ksuperkey (Use meta key to launch Albert)
```
cd ~/src/
git clone https://github.com/hanschen/ksuperkey.git
cd ksuperkey
make
sudo make install
```

## Install python evdev package (for joystick access)
`sudo pip install evdev`