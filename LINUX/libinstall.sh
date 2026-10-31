#!/bin/sh

################################################################
#
# A script to setup everything that needs be done on a
# 'virgin' RaspPi.
#
################################################################

################################################################
#
# Syntax-check this script before doing anything. "sh -n" parses
# the whole file without executing it, so a truncated download or
# a bad edit is caught here, up-front, before any package is
# installed or removed.
#
################################################################

if ! sh -n "$0"; then
  echo "ERROR: $0 failed its syntax check (sh -n), aborting." >&2
  exit 1
fi

################################################################
#
# a) determine the location of THIS script
#    (this is where the files should be located)
#    and assume this is in the pihpsdr directory
#
################################################################

SCRIPTFILE=`realpath "$0"`
THISDIR=`dirname "$SCRIPTFILE"`
TARGET=`dirname "$THISDIR"`
PIHPSDR="$TARGET/release/pihpsdr"

echo
echo "=============================================================="
echo "Script file absolute position  is $SCRIPTFILE"
echo "Pihpsdr target       directory is $TARGET"
echo "Icons and Udev rules  copied from $PIHPSDR"
echo "=============================================================="
echo

################################################################
#
# b) install lots of packages
# (many of them should already be there)
#
################################################################

echo "=============================================================="
echo
echo "... installing LOTS OF compiles/libraries/helpers"
echo
echo "=============================================================="

sudo apt-get update

# ------------------------------------
# Install standard tools and compilers
# ------------------------------------

sudo apt-get --yes install build-essential
sudo apt-get --yes install module-assistant
sudo apt-get --yes install vim
sudo apt-get --yes install make
sudo apt-get --yes install gcc
sudo apt-get --yes install g++
sudo apt-get --yes install gfortran
sudo apt-get --yes install git
sudo apt-get --yes install pkg-config
sudo apt-get --yes install cmake
sudo apt-get --yes install autoconf
sudo apt-get --yes install autopoint
sudo apt-get --yes install gettext
sudo apt-get --yes install automake
sudo apt-get --yes install libtool
sudo apt-get --yes install cppcheck
sudo apt-get --yes install dos2unix
sudo apt-get --yes install libzstd-dev

# ---------------------------------------
# Install libraries necessary for piHPSDR
# ---------------------------------------

sudo apt-get --yes install libfftw3-dev
sudo apt-get --yes install libgtk-3-dev
sudo apt-get --yes install libasound2-dev
sudo apt-get --yes install libssl-dev
sudo apt-get --yes install libcurl4-openssl-dev
sudo apt-get --yes install libusb-1.0-0-dev
sudo apt-get --yes install libi2c-dev
sudo apt-get --yes install libgpiod-dev
sudo apt-get --yes install libpulse-dev
sudo apt-get --yes install pulseaudio
sudo apt-get --yes install pipewire-pulse
sudo apt-get --yes install libpcap-dev
sudo apt-get --yes install libopus-dev
sudo apt-get --yes install libminiupnpc-dev
sudo apt-get --yes install libsqlite3-dev
sudo apt-get --yes install libwebsockets-dev
sudo apt-get --yes install zlib1g-dev

# python3-tk required for piSync
sudo apt-get --yes install python3-tk
#

#
# We have (tried to) install both pulseaudio and pipewire-pulse.
# When pipewire-pulse is providing the PulseAudio server, the stand-alone
# pulseaudio daemon is redundant and we would like to remove it.
#
# WARNING - do NOT use the old test:
#     RES=`sudo apt show pipewire-pulse | grep "^Installed" | wc -l`
# "apt show" prints archive metadata, not the install state, and always
# contains an "Installed-Size:" line which matches "^Installed". So RES was
# 1 for ANY package that merely exists in the repositories, even when
# pipewire-pulse was never installed, and pulseaudio was removed
# unconditionally. On desktops (KDE Plasma etc.) a session/meta-package
# depends on pulseaudio, so "apt remove pulseaudio" then cascaded into
# removing the whole desktop environment.
#
# Robust replacement:
#   1. Only continue if BOTH pulseaudio and pipewire-pulse are really
#      installed (checked via dpkg, not "apt show").
#   2. Simulate the removal first and only remove pulseaudio if nothing else
#      would be removed with it (i.e. no desktop meta-package depends on it).
#

pkg_installed() {
  dpkg-query -s "$1" 2>/dev/null | grep -q '^Status: .* installed$'
}

if pkg_installed pulseaudio && pkg_installed pipewire-pulse; then
  # Count any *other* packages that would be dragged out with pulseaudio.
  EXTRA=`LANG=C sudo apt-get --simulate --yes remove pulseaudio 2>/dev/null \
           | grep '^Remv ' | grep -vc '^Remv pulseaudio '`
  if [ "$EXTRA" -eq 0 ]; then
    echo "pipewire-pulse present and pulseaudio can be removed cleanly; removing pulseaudio"
    sudo apt-get --yes remove pulseaudio
  else
    echo "pipewire-pulse present, but removing pulseaudio would also remove $EXTRA other"
    echo "package(s) (a desktop environment may depend on it). Leaving pulseaudio installed."
  fi
fi

# ----------------------------------------------
# Install some fonts. Note that the much
# beloved "piboto" font, which is the old
# roboto font before its 2014 redesign,
# seems to be available on RaspPi only, and
# there it is pre-installed anyway.
#
# By defaults piHPSDR is using
# FreeSans  (--> fonts-freefont-otf)
# OpenSans  (--> fonts-open-sans)
# Roboto    (--> fonts-roboto)
#
# ----------------------------------------------

sudo apt-get install --yes fonts-open-sans
sudo apt-get install --yes fonts-freefont-otf
sudo apt-get install --yes fonts-roboto

# ----------------------------------------------
# Install standard libraries necessary for SOAPY
# NOTE: these library work for both V0.7 and V0.8
# SoapySDR. If these are added to the list of
# 'manually installed' Soapy software (see below)
# then they have to be removed HERE.
# ----------------------------------------------

sudo apt-get install --yes libaio-dev
sudo apt-get install --yes libavahi-client-dev
sudo apt-get install --yes libad9361-dev
sudo apt-get install --yes libiio-dev
sudo apt-get install --yes bison
sudo apt-get install --yes flex
sudo apt-get install --yes libxml2-dev
sudo apt-get install --yes librtlsdr-dev

################################################################ #
# c) download and install SoapySDR core, and support for some
#    radios
#
################################################################

echo "=============================================================="
echo
echo "... installing SoapySDR core"
echo
echo "=============================================================="

cd "$THISDIR/SoapySDR"
cd build
if [ -f ./CMakeCache.txt ]; then
   rm CMakeCache.txt
fi
make clean
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..
make
sudo make install
sudo ldconfig


echo "=============================================================="
echo
echo "... installing HackRF SoapySDR support"
echo
echo "=============================================================="

cd "$THISDIR"
yes | sudo apt-get install libhackrf-dev
cd SoapyHackRF
cd build
if [ -f ./CMakeCache.txt ]; then
   rm CMakeCache.txt
fi
make clean
cmake ..
make
sudo make install
sudo ldconfig

cd "$THISDIR"

echo "=============================================================="
echo
echo "... installing SoapySDR RTL-stick libraries"
echo
echo "=============================================================="

cd "$THISDIR/SoapyRTLSDR"
cd build
if [ -f ./CMakeCache.txt ]; then
   rm CMakeCache.txt
fi
make clean
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..
make
sudo make install
sudo ldconfig

cd "$THISDIR"

#
# Normally we would compile and install libiio-v0 and libad9361-v0
# manually from the sources here. But at this moment, the packages
# from the distro seem to work, and libiio-dev and libad9361-dev
# have been installed above. When switching to "manually installed"
# please remove the two apt-install commands for libiia-dev and
# libad9361-dev from the list at the top of this file.
#

echo "=============================================================="
echo
echo "... installing SoapySDR AdalmPluto libraries"
echo "... using libiio and libad9361 from the distro"
echo
echo "=============================================================="

cd "$THISDIR/SoapyPlutoSDR"
cd build
if [ -f ./CMakeCache.txt ]; then
   rm CMakeCache.txt
fi
make clean
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..
make
sudo make install
sudo ldconfig

cd "$THISDIR"

################################################################
#
# d) create start scripts, etc.  for pihpsdr
#    (Desktop icon and menu entry are created by piHPSDR-Improved-Installer.py,
#     since this script runs as root and cannot create them for the user)
#
################################################################

echo "=============================================================="
echo
echo "... creating start script (Desktop icon: see piHPSDR-Improved-Installer.py)"
echo
echo "=============================================================="

cat <<EOT > "$TARGET/pihpsdr.sh"
cd "$TARGET"
"$TARGET/pihpsdr" >log 2>&1
EOT
chmod +x "$TARGET/pihpsdr.sh"

cp "$PIHPSDR/piHPSDR_logo.png" "$TARGET"

################################################################
#
# ALL DONE.
#
################################################################

