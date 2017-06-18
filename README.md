# CCExtractor Sample Platform

This repository contains the code for a platform that manages a test suite 
bot, sample upload and more. This platform allows for a unified place to 
report errors, submit samples, view existing samples and more. It was 
originally developed during GSoC 2015 and rewritten during GSoC 2016. During
GSoC 2017 it's being further improved.

you can visit 
[CCExtractor Submission Platform](https://sampleplatform.ccextractor.org/) to 
see the live version of the platform.

## Concept

While CCExtractor is an awesome tool and it works flawlessly most of the time,
bugs occur occasionally (as with all existing software). These are usually 
reported through a variety of channels (private email, mailing list, GitHub, 
and so on...).

The aim of this project is to build a platform, which is accessible to 
everyone (after signing up), that provides a single place to upload, view 
samples and associated test results.

## Installation

### Requirements

* Nginx (Other possible when modifying the sample download section)
* Python 2.7 (Flask and other dependencies)
* MySQL
* Pure-FTPD with mysql

### Automated install

Automated install only works for the platform section, **not** for the KVM
functionality. To install the VM's for KVM, see 
[the installation guide](install/ci-vm/installation.md).

#### Linux

Clone the latest sample-platform repository from 
https://github.com/canihavesomecoffee/sample-platform.

```
git clone https://github.com/canihavesomecoffee/sample-platform.git
```

The `sample-repository` directory needs to be accessible by `www-data`. The
recommended directory is thus `/var/www/`.

Next, navigate to the `install` folder and run `install.sh` with root 
permissions.

```
cd sample-platform/install/
sudo ./install.sh
```    

The `install.sh` will begin downloading and updating all the necessary 
dependencies. Once done, it'll ask to enter some details in order to set up 
the sample-platform. After filling in these the platform should be ready for
use.

Please read the below troubleshooting notes in case of any error or doubt.

#### Windows

* Install cygwin (http://cygwin.com/install.html). When cygwin asks which
 packages to install, select Python, MySql, virt-manager and openssh.
* Start a terminal session once installation is complete.
* Install Nginx (see http://nginx.org/en/docs/windows.html)
* Install XMing XServer and setup Putty for ssh connections.
* Virt-manager can call ssh to make the connection to KVM Server and should be 
able to run virsh and send commands to it. 
* Follow the steps from the Linux installation from within the Cygwin terminal
to complete the platform's installation.

#### Troubleshooting

* Both installation and running the platform requires root (or sudo).
* The configuration of the sample platform assumes that no other application
already runs on port 80. A default installation of nginx leaves a `default` 
config file behind, so it's advised to delete that and stop other 
applications that use the port.

**Note : Do not forget to do `service nginx reload` and 
`service platform start` after making any changes to the nginx configuration
or platform configuration.**
* SSL is a required. If the platform runs on a publicly accessible server, 
it's **recommended** to use a valid certificate. 
[Let's Encrypt](https://letsencrypt.org/) offers free certificates. For local
testing, a self-signed certificate can be enough.
* When the server name is asked during installation, enter the domain name 
that will run the platform. E.g., if the platform will run locally, enter 
`localhost` as the server name.
* In case of a `502 Bad Gateway` response, the platform didn't start 
correctly. Manually running `bootstrap_gunicorn.py` (as root!) can help to 
determine what goes wrong. The snippet below shows how this can be done:

```
cd /var/www/sample-platform/
sudo python bootstrap_gunicorn.py
```

* If `gunicorn` boots up successfully, most relevant logs will be stored in
 the `logs` directory. Otherwise they'll likely be in `syslog`.

### Nginx configuration for X-Accel-Redirect

To serve files without any scripting language overhead, the X-Accel-Redirect 
feature of Nginx is used. To enable it, a special section (as seen below) 
needs to be added to the nginx configuration file:

```
location /protected/ {
    internal;
    alias /path/to/storage/of/samples/; # Trailing slash is important!
}
```

More info on this directive is available at the 
[Nginx wiki](http://wiki.nginx.org/NginxXSendfile).

Other web servers can be configured too (see this excellent 
[SO](http://stackoverflow.com/a/3731639) answer), but will require a small 
modification in the relevant section of the `serve_file_download` definition 
in `mod_sample/controllers.py` which is responsible for handling the download
requests.

### File upload size for HTTP

In order to accept big files through HTTP uploads, some files need to be 
adapted.

#### Nginx

If the upload is too large, Nginx will throw a 
`413 Request entity too large`. To remedy this error, modify the next section
in the nginx config:

```
# Increase Nginx upload limit
client_max_body_size 1G;
```

### Pure-FTPD configuration

Besides HTTP, there is also an option available to upload files through FTP.
As the privacy of individual sample submitters should be respected, each user
must get it's own FTP account. However, system accounts pose a possible 
security threat, so virtual accounts (using MySQL) are to be used instead. 
Virtual users also offer the added benefit of easier management.

#### Pure-FTPD installation

`sudo apt-get install pure-ftpd-mysql`

If requested, answer the following questions as follows:

```
Run pure-ftpd from inetd or as a standalone server? <-- standalone
Do you want pure-ftpwho to be installed setuid root? <-- No
```

#### Special group & user creation

All MySQL users will be mapped to this user. A group and user id that is
still available should be chosen.

```
sudo groupadd -g 2015 ftpgroup
sudo useradd -u 2015 -s /bin/false -d /bin/null -c "pureftpd user" -g ftpgroup ftpuser
```

#### Configure Pure-FTPD

Edit the `/etc/pure-ftpd/db/mysql.conf` file (in case of Debian/Ubuntu) so it
matches the next configuration:

```
MYSQLSocket      /var/run/mysqld/mysqld.sock
# user from the DATABASE_USERNAME in the configuration, or a separate one
MYSQLUser       user 
# password from the DATABASE_PASSWORD in the configuration, or a separate one
MYSQLPassword   ftpdpass
# The database name configured in the DATABASE_SOURCE_NAME dsn string in the configuration
MYSQLDatabase   pureftpd
# For now we use plaintext. While this is terribly insecure in case of a database leakage, it's not really an issue, 
# given the fact that the passwords for the FTP accounts will be randomly generated and hence do not contain sensitive 
# user info (we need to show the password on the site after all).
MYSQLCrypt      plaintext
# Queries
MYSQLGetPW      SELECT Password FROM ftpd WHERE User="\L" AND status="1" AND (ipaccess = "*" OR ipaccess LIKE "\R")
MYSQLGetUID     SELECT Uid FROM ftpd WHERE User="\L" AND status="1" AND (ipaccess = "*" OR ipaccess LIKE "\R")
MYSQLGetGID     SELECT Gid FROM ftpd WHERE User="\L" AND status="1" AND (ipaccess = "*" OR ipaccess LIKE "\R")
MYSQLGetDir     SELECT Dir FROM ftpd WHERE User="\L" AND status="1" AND (ipaccess = "*" OR ipaccess LIKE "\R")
MySQLGetQTAFS   SELECT QuotaFiles FROM ftpd WHERE User="\L" AND status="1" AND (ipaccess = "*" OR ipaccess LIKE "\R")
# Override queries for UID & GID
MYSQLDefaultUID 2015 # Set the UID of the ftpuser here
MYSQLDefaultGID 2015 # Set the GID of the ftpgroup here
```

Next, a file called `ChrootEveryone` must be created, so that the individual
users are jailed:

```
echo "yes" > /etc/pure-ftpd/conf/ChrootEveryone
```

The same needs to be done for `CreateHomeDir` and `CallUploadScript`:

```
echo "yes" > /etc/pure-ftpd/conf/CreateHomeDir
echo "yes" > /etc/pure-ftpd/conf/CallUploadScript
```

Also `/etc/default/pure-ftpd-common` needs some modification:

```
UPLOADSCRIPT=/path/to/cron/upload.sh
UPLOADUID=1234 # User that owns the upload.sh script
UPLOADGID=1234 # Group that owns the upload.sh script
```

When necessary, an appropriate value in the Umask file 
(`/etc/pure-ftpd/conf/Umask`) should be set as well.

After this you Pure-FTPD can be restarted using 
`sudo /etc/init.d/pure-ftpd-mysql restart`

Note: if there is no output saying: 
`Restarting ftp upload handler: pure-uploadscript.`, the uploadscript will
need to be started. This can be done using the next command (assuming 1000 is
the `gid` and `uid` of the user which was specified earlier):

```
sudo pure-uploadscript -u 1000 -g 1000 -B -r /home/path/to/src/cron/upload.sh
```

To check if the upload script is running, the next command can help:
`ps aux | grep pure-uploadscript`. If it still doesn't work, rebooting the 
server might help as well.

## Contributing

All information with regards to contributing can be found here:
[contributors guide](.github/CONTRIBUTING.md).

## Security

Even though many precautions have been taken to ensure that this software is
stable and secure, bugs can occur. In case there is a security related issue, 
please send an email to ccextractor@canihavesome.coffee (GPG key 
[0xF8643F5B](http://pgp.mit.edu/pks/lookup?op=vindex&search=0x3AFDC9BFF8643F5B),
fingerprint 53FF DE55 6DFC 27C3 C688 1A49 3AFD C9BF F864 3F5B) instead of 
using the issue tracker. This will help to prevent abuse while the issue is 
being resolved.
