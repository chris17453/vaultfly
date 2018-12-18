# vaultfly
Ansible login automation using ansible vault with templating and password tokens

## What
- vaultfly is for automating ssh login when you need to use a token

## Install

```bash
pip install vaultfly --user
```

## Tokens (the hard part)
- To generate the token, you need access to the token definition file.
- Most likely you dont have access to that. 
- The work arround is to generate your own and use that.
- I use 'python-vipaccess2'. It will generate a Symantec compatible token
- pip install python-vipaccess2 or pipenv....
- instructions can be found at https://github.com/chris17453/vipaccessUI

## Help

```bash
$ vaultfly

usage: vault-fly [-h] [-i] [-b] [-r] [-v VAULT_FILE] [-vt VAULT_TEMPLATE]
                 [-c CONFIG_FILE] [-p PASSWORD_FILE] [-t] [-sc] [-sv] [-vvv]

Create ansible vault login credentials on the fly.

optional arguments:
  -h, --help            show this help message and exit

Commands:
  -i, --init            init user config
  -b, --build           build a new vault file
  -r, --random-pass     generate a random password and save it to the password
                        file

Config:
  -v VAULT_FILE, --vault-file VAULT_FILE
                        login vault file to create
  -vt VAULT_TEMPLATE, --vault-template VAULT_TEMPLATE
                        create vault file with this template
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        user config created from 'init'
  -p PASSWORD_FILE, --password-file PASSWORD_FILE
                        single line text file with used for vault password
  -t, --token           use token with password in (password+token)

Display:
  -sc, --show-config    view config file
  -sv, --show-vault     view vault file
  -vvv, --verbose       Display more execution info

```


## Walkthrough
```bash
# create a user config with a random password file
[test]$  vaultfly -i -p test.pass -c test.config

Password file is invalid, Create random password? [y/N] y

Enter SSH credentials that anssible will connect with:
User [nd]:chris17453
Password: 

# view password file
[test]$ cat test.pass
iroen@yh#Ts5fV04*BWcvRFj$HLDazZd

# view config file
[test]$ cat test.config 
$ANSIBLE_VAULT;1.1;AES256
62633361656165383232353630303864343531663530373131323363623535323362333564616462
6137633635313839303137363965656262376238643238310a356432313061333863363737613939
64656537326532623531633833663933363534316530383730646539303865333765353266643437
3463383330663731330a343231323139613062333462633865636463643234643634636238316562
65633135386636356438663434633538653239303732333732316635636466336263353162336434
3332376162626231653630336636303734333035636538386236

# create new vault file on the fly
[test]$  vaultfly -b -p test.pass -c test.config -v test.vault

# view test vault
[test]$  cat test.vault
$ANSIBLE_VAULT;1.1;AES256
34333735653766373361383963643037666234626231613461633166623334613731363063623666
3763343062333337653637303736363061623962373762610a613632393335666565333633663333
37613430653936663230346364643866616239326235306262373432323366316337633965383663
3361363535343661350a323266353536626635666364376432303966326635626464383565323763
33326239303863393566396464396438663533316336623237353862363734373732366666396433
35656665313163306662613363306338383163643762666537623364653533333466376537663261
61326535316331366661663332323861316436303731613165333638663463363262396630633534
31653230626165613431623235336334613139333631623665313435313139333931653062326534
3163

#show decrypted vault
[test]$ vaultfly -p test.pass -c test.config -v test.vault -sv
ansible_connection: ssh
ansible_ssh_pass: mypassword
ansible_ssh_user: chris17453

# display template for next example
[test]$ cat template.vault
bob: 4324

# create vault on the fly with token using a template 
# display unencrypted vault file (the display option is for convienence)

[test]$ vaultfly -b  -p test.pass \
                 -c test.config \
                 -v test.vault \
                 -vt template.vault \
                 -t

ansible_connection: ssh
ansible_ssh_pass: mypassword803883
ansible_ssh_user: chris17453
bob: 4324

```


## How to use with ansible?
- First I created a template called tpl.vault
```yaml
ansible_become: true
ansible_become_method: su
ansible_user: 'user'
ansible_become_exe: 'sudo  su -'
```
- Next then made an inventory - > inventory.ini
```yaml
[test]
test-box1.com.internal
test-box2.com.internal
```
- Then I made an ansible play -> copy.yaml
```yaml
---
- hosts: test
  gather_facts: False
  tasks:
  - name: Copy stuff if this is -> test-box1.com.internal
    copy:
      src: ../code/
      dest: /tmp/placetoputstuff
      owner: user
      group: group
    when: inventory_hostname == "test-box1.com.internal"

  - name: Copy stuff if this is -> test-box2.com.internal
    copy:
      src: ../code/
      dest: /tmp/different_placetoputstuff
      owner: user
      group: group
    when: inventory_hostname == "test-box2.com.internal"
```
- Finally I run the play everytime I want to upload some files
```bash

#build a new vault with a token
vaultfly -b -t -vt tpl.vault -p my-pass-file -c my-config-file -v group_vars/all
# run the play
ansible-playbook -i inventory.ini copy.yaml
```

## updates
- I will make updates as required giving time

## notes
- 'make standalone' will build no dependency executable in "dist/"
