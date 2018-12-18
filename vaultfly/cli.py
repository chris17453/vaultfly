import subprocess
import sys
import argparse
import oath
import os
import getpass
import random
import yaml


debug=False
# found this gem on stack exchange. edit for py3 support
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        try:
            choice = raw_input().lower()
        except:
            choice = input().lower()
            pass
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def get_user(prompt,empty_ok=True):
    """Prompt user for input
    If empty_ok=False, it will continue looping until satisfied
    
    returns: string"""

    choice=""
    if empty_ok!=True:
        while choice.strip() == '':
            sys.stdout.write(prompt)
            try:
                choice = raw_input().lower()
            except:
                choice = input().lower()
                pass
        return choice
    else:
        sys.stdout.write(prompt)
        try:
            choice = raw_input().lower()
        except:
            choice = input().lower()
        return choice

def info(data):
    """display debugging info if verbosity is set to TRUE"""

    if debug==True:
        sys.stdout.write(data)

def id_generator(passlen = 8 ):
    """generate a random id of n lenght"""

    s = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz01234567890!@#$%^&*()?"
    p =  "".join(random.sample(s,passlen ))
    return p

#generates token from vipaccess
def get_access_token():
    """Generate an OTP access token from .vipaccess configuration 
        in your home dir"""

    info("Generating Token")
    dotfile=os.path.expanduser('~/.vipaccess')
    if os.path.exists(dotfile) is False:
        raise Exception("vipaccess not configured. No token can be created")

    with open(dotfile, "r") as dotfile:
        d = dict( l.strip().split(None, 1) for l in dotfile )
        if 'version' not in d:
            raise Exception('%s does not specify version' % dotfile)
        elif d['version'] != '1':
            raise Exception("%s specifies version %r, rather than expected '1'" 
                            % (dotfile, d['version']))
        elif 'secret' not in d:
            raise Exception('%s does not specify secret' % dotfile)
        secret = d.get('secret')
    try:
        key = oath._utils.tohex( 
            oath.google_authenticator.lenient_b32decode(secret) 
            )
        token=oath.totp(key)
        return  token
    except Exception as e:
        raise Exception('error interpreting secret as base32: %s' % e)
        

def create_user_vault(password_file,config_file):
    """Create a vaultfly configuration file, 
        which is encrypted by ansible vault"""

    info("Creating Config")
    info(" Config File  : {}".format(config_file))
    info(" Password File: {}".format(password_file))


    if validate_password_file_exists(password_file)==False:
        if query_yes_no("""Password file is invalid, Create random password?""","no"):
            create_password_file(password_file)
        else:
            raise Exception("""Password file is invalid: 
            This is required to create a vault.
            It's what is used to encrypt/decrypt the vaults.""")


    if validate_config_file_exists(config_file)==True:
        if False ==query_yes_no("Config exists, overwrite?","no"):
            raise Exception ("Aborting config, user canceled")
    try:
        sys.stdout.write("\n\nEnter SSH credentials that anssible will connect with\n")
        loggedin_user_name=getpass.getuser()
        user = get_user("User [{}]:".format(loggedin_user_name),empty_ok=True)
        pwd=''
        if not user:
            user=loggedin_user_name
        while pwd.strip() =='':
            pwd = getpass.getpass()

        configuration={'username':user,'password':pwd}
        
        with open(config_file, 'w') as outfile:
            yaml.dump(configuration, outfile, default_flow_style=False)

        FNULL = open(os.devnull, 'w')
        subprocess.call(["ansible-vault",
                        "encrypt",
                        config_file,
                        "--vault-password-file",
                        password_file],
                        stdout=FNULL,
                        stderr=subprocess.STDOUT)
        FNULL.close()

    except Exception as ex:
        raise Exception("Error encrypting configuration vault: {}".format(ex))
        
def create_password_file(password_file):
    """Create a single line password file for ansible vault.
        The password is 32 characters long.
        
        ***Add this file to your gitignore.
        """

    info("Creating Random Password")
    info(" Password File: {}".format(password_file))

    try:
        if validate_password_file_exists(password_file)==True:
            question="Vault password file exists, overwrite?"
            if False==query_yes_no(question, default="no"):
                raise Exception ("Aborting password creation, user canceled")

        pwd = id_generator(32)
        f= open(password_file,"w+")
        f.write("{}".format(pwd))
        f.close()       
    except Exception as ex:
        raise Exception("Error creating password file: {}".format(ex))

def validate_config_file_exists(config_file):
    """Validate if the config file exists
        results: bool"""

    if os.path.exists(config_file) is False:
        return False
    return True

def validate_password_file_exists(password_file):
    """ Validate if the password file exists
        results: bool"""

    if os.path.exists(password_file) is False:
        return False
    return True

def validate_vault_file_exists(vault_file):
    """ Validate if the vault file exists
        results: bool"""

    if os.path.exists(vault_file) is False:
        return False
    return True

def view(password_file,filename):
    """Display an encrypted ansible vault file to stdio"""
    data=subprocess.check_output( ["ansible-vault", 
                                        "view",filename,
                                        "--vault-password-file",
                                        password_file], 
                                        stderr=subprocess.STDOUT)
    sys.stdout.write(yaml.dump(yaml.load(data), default_flow_style=False))
    sys.stdout.write("\n")
    
def view_config(password_file,config_file):
    """view the plain text version of an ansible vault encrypted
        vaultfly configuration"""

    info("Displaying Config")
    info(" Config File  : {}".format(config_file))
    info(" Password File: {}".format(password_file))
    if validate_config_file_exists(config_file)==False:
        sys.stdout.write("Config file does not exist\n")
    else:
        view(password_file,config_file)

def view_vault(password_file,vault_file):
    """view the plain text version of an ansible vault file
    """

    info("Displaying Vault")
    info(" Vault File   : {}".format(vault_file))
    info(" Password File: {}".format(password_file))
    if validate_vault_file_exists(vault_file)==False:
        sys.stdout.write("Vault file does not exist\n")
    else:
        view(password_file,vault_file)

def load_template(template_file):
    """Load a yaml template file"""

    if os.path.exists(template_file)==False:
        raise Exception("Template file does not exist")
    
    with open(template_file, 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as ex:
            raise Exception("Cannot load template: {}".format(ex))

def create_vault_file(vault_file,password_file,config_file,vault_template=None,use_token=None):
    """Create an ansible vault from a vaultfly configuration
        and optional template """

    info("Creating Vault")
    info(" Config File  : {}".format(config_file))
    info(" Password File: {}".format(password_file))
    info(" Vault File   : {}".format(vault_file))

    if  validate_config_file_exists(config_file) is False:
        raise Exception ("config file missing or invalid")

    if validate_password_file_exists(password_file) is False:
        # TODO validate length of line of text in password file
        raise Exception( "password file missing or invalid")

    
    try:
        # get the encrypted password in ansible vault
        yaml_data=subprocess.check_output( ["ansible-vault", 
                                        "view",config_file,
                                        "--vault-password-file",
                                        password_file], 
                                        stderr=subprocess.STDOUT)
        
        configuration=yaml.load(yaml_data)
        if vault_template:
            template=load_template(vault_template)
        else:
            template=None

        user=configuration['username']
        password=configuration['password']

        if password==None:
            raise Exception("password is null in config")
        if user is None:
            raise Exception("user is null in config")

        
        if template:
            configuration=template
        else:
            configuration={}

        configuration['ansible_connection']='ssh'
        configuration['ansible_ssh_user']=user
                        
        if use_token==True:
            #grab current token
            access_token=get_access_token()
            configuration['ansible_ssh_pass']='{}{}'.format(
                                password.strip(),
                                access_token.strip())
        else:
            configuration['ansible_ssh_pass']='{}'.format(password.strip())

    
        with open(vault_file, 'w') as outfile:
            yaml.dump(configuration, outfile, default_flow_style=True)

        FNULL = open(os.devnull, 'w')
        #create new ansible vault file for current token
        subprocess.call(["ansible-vault", 
                        "encrypt",
                        vault_file,
                        "--vault-password-file",password_file],
                        stdout=FNULL,
                        stderr=subprocess.STDOUT)
        FNULL.close()

    except Exception as ex:
        raise Exception ("Create Vault:{}".format(ex))

def cli_main():
    global debug
    p = argparse.ArgumentParser("vault-fly",
        description="Create ansible vault login credentials on the fly.")
    
    
    vault_help     ="login vault file to create"
    token_help     ="use token with password in (password+token)"
    init_help      ="init user config"
    build_help     ="build a new vault file"
    show_c_help    ="view config file"
    show_v_help    ="view vault file"
    vault_tpl_help ="create vault file with this template"
    config_help    ="user config created from 'init'"
    pass_help      ="single line text file with used for vault password"
    random_pwd     ="generate a random password and save it to the password file"
    verbose_help   ="Display more execution info"

    vault_tpl =None
    vault_pwd ="vault.pwd"
    user_cfg  ="user.config"
    vault     ="vault"
    
    # these do things
    commands = p.add_argument_group("Commands")
    commands.add_argument('-i','--init'        , help= init_help  , action= 'store_true')
    commands.add_argument('-b','--build'       , help= build_help , action= 'store_true')
    commands.add_argument('-r','--random-pass' , help= random_pwd , action= 'store_true')
    
    # these are data options
    config = p.add_argument_group("Config")
    config.add_argument('-v' ,'--vault-file'     , help= vault_help , default= vault)
    config.add_argument('-vt' ,'--vault-template', help= vault_tpl_help , default= vault_tpl)
    config.add_argument('-c'  ,'--config-file'   , help= config_help, default= user_cfg)
    config.add_argument('-p'  ,'--password-file' , help= pass_help  , default= vault_pwd)
    config.add_argument('-t'  ,'--token'         , help= token_help , action= "store_true")
    
    display = p.add_argument_group("Display")
    display.add_argument('-sc','--show-config', help= show_c_help , action= 'store_true')
    display.add_argument('-sv','--show-vault' , help= show_v_help , action= 'store_true')
    display.add_argument('-vvv','--verbose'   , help= verbose_help, action= "store_true")
    
    args=p.parse_args()
    try:
        if args.verbose:
            debug=True
        #if no action is set... exit
        if args.init is False and \
           args.build is False and  \
           args.random_pass is False and \
           args.show_config is False and \
           args.show_vault is False:
            p.print_help()
            return

        if args.random_pass and args.build and args.init is False:
            raise Exception("You cant create a random pass without an init.")
            
        if args.random_pass: 
            create_password_file(args.password_file)

        if args.init:
            create_user_vault(  config_file  = args.config_file,
                                password_file= args.password_file)

        if args.build: 
            create_vault_file(
                vault_file    = args.vault_file,
                config_file   = args.config_file,
                password_file = args.password_file,
                vault_template= args.vault_template,
                use_token     = args.token)
  
        # display options come last, so that we can see the changes
        if args.show_config:
            view_config(  config_file   = args.config_file,
                          password_file= args.password_file)

        if args.show_vault:
            view_vault(  vault_file   = args.vault_file,
                         password_file= args.password_file)
    
  
  
    except Exception as ex:
        sys.stdout.write("{}\n".format(ex))

    
# entry point
if __name__=='__main__':
    cli_main()

