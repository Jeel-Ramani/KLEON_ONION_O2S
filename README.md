# KLEON_ONION_O2S

### Run the following if omega is not on the 23.05 version
```bash 
cd /tmp
wget http://repo.onioniot.com.s3.amazonaws.com/omega2/images/openwrt-23.05/onion_omega2p-23.05.3-20250205.bin
sysupgrade -F -n -v 
```

### First expand the storage of the onion omega 
```bash
#please ensure the sd card is inserted
mkdir /mnt/mmcblk0p1
mount /dev/mmcblk0p1 /mnt/
mount /dev/mmcblk0p1 /mnt/ ; tar -C /overlay -cvf - . | tar -C /mnt/ -xf - ; umount /mnt/
opkg update
opkg install block-mount
block detect > /etc/config/fstab
vi /etc/config/fstab
```
### Look for the line

```bash
option  target  '/mnt/<device name>'
```
### and change it to:

```bash
option target '/overlay'
```
###Then, look for the line:

```bash
option  enabled '0'
```
### and change it to

```bash 
option  enabled '1'
```

### steps for swap memory
```bash
opkg update
opkg install swap-utils block-mount
dd if=/dev/zero of=/overlay/swap.page bs=1M count=384
mkswap /overlay/swap.page
swapon /overlay/swap.page
uci set fstab.@mount[0].enabled='1'
uci commit fstab
/etc/init.d/fstab enable
block mount
block umount;block mount
vi /etc/rc.local
```
### in this file past the following lines
```bash
### activate the swap file on an external USB drive
SWAP_FILE="/overlay/swap.page"
if [ -e "$SWAP_FILE" ]; then
        swapon $SWAP_FILE
fi
```
### Installing python and dependencies
```bash
opkg update
opkg install python3
opkg install python3-pip
pip install pytz requests pyserial pymodbus requests dotenv flask
```

### create startup script using the following command 
```bash
vi etc/init.d/startup_script
```
### add the following lines in that file
```bash
#!/bin/sh /etc/rc.common
START=90

USE_PROCD=1


start_service() {
        procd_open_instance
        procd_set_param command usr/bin/python3 onion-config/main.py
#        procd_append_param command [COMMAND ARGUMENTS]     # optionally append command parameters
        procd_set_param respawn  # respawn the service if it exits
#        procd_set_param stdout 1 # forward stdout of the command to logd
#        procd_set_param stderr 1 # same for stderr
        procd_close_instance
}
```
### run the following command after saving file
```bash
chmod +x etc/init.d/startup_script
etc/init.d/startup_script enable
etc/init.d/startup_script start
```

### create aanother startup file using the following command

```bash
vi etc/init.d/modbus_startup
```
### add the following lines in that file
```bash
#!/bin/sh /etc/rc.common
START=90

USE_PROCD=1


start_service() {
        procd_open_instance
        procd_set_param command usr/bin/python3 onion-config/modbus3.py
#        procd_append_param command [COMMAND ARGUMENTS]     # optionally append command parameters
        procd_set_param respawn  # respawn the service if it exits
#        procd_set_param stdout 1 # forward stdout of the command to logd
#        procd_set_param stderr 1 # same for stderr
        procd_close_instance
}
```
### Run the following command after saving that file
```bash
chmod +x etc/init.d/modbus_startup
etc/init.d/modbus_startup enable
etc/init.d/modbus_startup start
```
### for hostname and wifi run the following command and change XXXX to the device number
```bash
uci set system.@system[0].hostname='omega-UbiqO2S-9A60'
uci commit system

uci set wireless.default_radio0.ssid='UbiqO2S-9A60'
uci commit wireless


uci set wireless.default_radio0.key='KleonO2S'
uci commit wireless
wifi reload
```

