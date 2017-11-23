#!/usr/bin/env python3
# coding=utf-8
import getpass
import os
import sys
from io import StringIO

import sh


def red(text):
    return '\033[0;31m{0}\033[0m'.format(text)


def green(text):
    return '\033[00;32m{0}\033[0m'.format(text)


def blue(text):
    return '\033[00;34m{0}\033[0m'.format(text)


def grey(text):
    return '\033[00;37m{0}\033[0m'.format(text)


OUTPUT_WIDTH = 80
LONGEST_STATUS = len('already installed')
HOME = os.environ.get('HOME')
VERBOSE = True

"""
Wishlist: argparse/positional args(click/fire?)
    - verbose
    - only pull all gits
    - gui related
"""


def install_apt_package(package, password):
    try:
        dpkg_query_result = sh.dpkg_query('-W', "-f='${Status}'", package)
    except sh.ErrorReturnCode_1:
        if password is None:
            p = sh.apt_get('install', '-y', package, _bg=True)
        else:
            with sh.contrib.sudo(password=password, _with=True):
                p = sh.apt_get('install', '-y', package, _bg=True)
        print('{package:.<{spacing}}{status:.>29}'.format(package=package, status=blue('Installing'),
                                                          spacing=OUTPUT_WIDTH-LONGEST_STATUS), end='\r')
        p.wait()
        print('{package:.<{spacing}}{status:.>29}         '.format(package=package, status=green('Installed!'),
                                                                   spacing=OUTPUT_WIDTH-LONGEST_STATUS))

    else:
        print('{package:.<{spacing}}{status:.>29}'.format(package=package, status=grey('already installed'),
                                                          spacing=OUTPUT_WIDTH-LONGEST_STATUS))


def file_exists(path):
    try:
        # noinspection PyCallingNonCallable
        sh.test('-e', path)
    except sh.ErrorReturnCode_1:
        return False
    else:
        return True


def install_from_curl(name, test_file, curl_args, mkdir=None):
    if file_exists(test_file):
        print('{package:.<{spacing}}{status:.>29}'.format(package=name, status=grey('already installed'),
                                                          spacing=OUTPUT_WIDTH - LONGEST_STATUS))
    else:
        if mkdir:
            [sh.mkdir('-p', to_make) for to_make in mkdir]
        p = sh.curl(*curl_args, _bg=True)
        print('{package:.<{spacing}}{status:.>29}'.format(package=name, status=blue('installing'),
                                                          spacing=OUTPUT_WIDTH - LONGEST_STATUS), end='\r')
        p.wait()
        print('{package:.<{spacing}}{status:.>29}         '.format(package=name, status=green('Installed!'),
                                                                   spacing=OUTPUT_WIDTH - LONGEST_STATUS))


def install_from_git(name, repo_dir, clone_args, workdir=HOME, sudo_link_after=None):
    if file_exists(repo_dir):
        sh.cd(repo_dir)  # workdir is above where we clone
        print('{package:.<{spacing}}{status:.>29}\r'.format(package=name, status=blue('updating'),
                                                            spacing=OUTPUT_WIDTH - LONGEST_STATUS), end='\r')
        buf = StringIO()
        p = sh.git.pull(_bg=True, _out=buf)
        p.wait()
        if 'up-to-date' in buf.getvalue():
            print('{package:.<{spacing}}{status:.>29}         '.format(package=name, status=grey('up to date'),
                                                                       spacing=OUTPUT_WIDTH - LONGEST_STATUS))
        else:
            print('{package:.<{spacing}}{status:.>29}         \n'.format(package=name, status=green('updated'),
                                                                         spacing=OUTPUT_WIDTH - LONGEST_STATUS))
            if VERBOSE:
                print(buf.getvalue())
    else:
        sh.cd(workdir)
        print('{package:.<{spacing}}{status:.>29}\r'.format(package=name, status=blue('installing'),
                                                            spacing=OUTPUT_WIDTH - LONGEST_STATUS), end='\r')
        p = sh.git.clone(*clone_args, _bg=True)
        p.wait()
        print('{package:.<{spacing}}{status:.>29}         '.format(package=name, status=green('installed'),
                                                                   spacing=OUTPUT_WIDTH - LONGEST_STATUS))


def install_from_script(name, test_file, remote_script_location):
    if file_exists(test_file):
        print('{package:.<{spacing}}{status:.>29}'.format(package=name, status=grey('already installed'),
                                                          spacing=OUTPUT_WIDTH - LONGEST_STATUS))
    else:
        print('{package:.<{spacing}}{status:.>29}'.format(package=name, status=blue('installing'),
                                                          spacing=OUTPUT_WIDTH - LONGEST_STATUS))
        sh.sh('-c', '"$(curl -fsSL {})"'.format(remote_script_location), _fg=True)
        print('{package:.<{spacing}}{status:.>29}'.format(package=name, status=blue('installed'),
                                                          spacing=OUTPUT_WIDTH - LONGEST_STATUS))


def main():
    print(green('#' * OUTPUT_WIDTH))
    print(green('# {0:^{width}} #').format('DJetelina .files', width=OUTPUT_WIDTH-4))
    print(green('#' * OUTPUT_WIDTH))
    sh.git('pull')

    if sh.whoami() == 'root':
        password = None
    else:
        password = getpass.getpass(prompt='[sudo] password for {}: '.format(getpass.getuser()))
        with sh.contrib.sudo(password=password, _with=True):
            try:
                sh.sudo('-n', 'true')
            except sh.ErrorReturnCode_1:
                print(red('Invalid password :('))
                sys.exit(1)

    target = input(blue('Install GUI related packages? (y/n): '))
    if target == 'y':
        gui_packages = True
    elif target == 'n':
        gui_packages = False
    else:
        print(red('Unrecognized input'))
        sys.exit(1)

    apt_basic = ['python2.7', 'shellcheck', 'python-pip', 'python3-pip', 'zsh', 'curl', 'vim', 'apt-listchanges']
    apt_gui = ['i3', 'i3lock', 'i3blocks', 'i3status']

    print(green('\n{0:^{width}}').format('aptitude basic', width=OUTPUT_WIDTH))
    print(green('=' * OUTPUT_WIDTH))
    for package in apt_basic:
        install_apt_package(package, password)
    if gui_packages:
        print(green('\n{0:^{width}}').format('aptitude GUI', width=OUTPUT_WIDTH))
        print(green('=' * OUTPUT_WIDTH))
        for package in apt_gui:
            install_apt_package(package, password)

    pip2_packages = ['powerline-status']
    default_pip_packages = ['pydocstyle', 'flake8', 'pipenv']

    try:
        sh.which('pip2')
    except sh.ErrorReturnCode_1:
        from sh import pip as pip2
    else:
        from sh import pip2

    print(green('\n{0:^{width}}').format('python2 packages', width=OUTPUT_WIDTH))
    print(green('=' * OUTPUT_WIDTH))
    installed_packages = [installed.split('=')[0] for installed in pip2('freeze', _iter=True)]
    for package in pip2_packages:
        if package in installed_packages:
            print('{package:.<{spacing}}{status:.>29}'.format(package=package, status=blue('updating'),
                                                              spacing=OUTPUT_WIDTH - LONGEST_STATUS), end='\r')
        else:
            print('{package:.<{spacing}}{status:.>29}'.format(package=package, status=blue('Installing'),
                                                              spacing=OUTPUT_WIDTH - LONGEST_STATUS), end='\r')
        pip2('-q', '-q', '-q', 'install', '--user', '--upgrade', package)

        print('{package:.<{spacing}}{status:.>29}         '.format(package=package, status=green('updated'),
                                                                   spacing=OUTPUT_WIDTH - LONGEST_STATUS))

    print(green('\n{0:^{width}}').format('python (default interpreter) packages', width=OUTPUT_WIDTH))
    print(green('=' * OUTPUT_WIDTH))
    installed_packages = [installed.split('=')[0] for installed in sh.pip('freeze', _iter=True)]
    for package in default_pip_packages:
        if package in installed_packages:
            print('{package:.<{spacing}}{status:.>29}'.format(package=package, status=blue('updating'),
                                                              spacing=OUTPUT_WIDTH - LONGEST_STATUS), end='\r')
        else:
            print('{package:.<{spacing}}{status:.>29}'.format(package=package, status=blue('Installing'),
                                                              spacing=OUTPUT_WIDTH - LONGEST_STATUS), end='\r')
        sh.pip('-q', '-q', '-q', 'install', '--user', '--upgrade', package)

        print('{package:.<{spacing}}{status:.>29}         '.format(package=package, status=green('updated'),
                                                                   spacing=OUTPUT_WIDTH - LONGEST_STATUS))

    print(green('\n{0:^{width}}').format('vim', width=OUTPUT_WIDTH))
    print(green('=' * OUTPUT_WIDTH))
    install_from_curl('pathogen', '~/.vim/autoload/pathogen.vim'.replace('~', HOME),
                      ['-LSso', '~/.vim/autoload/pathogen.vim'.replace('~', HOME), 'https://tpo.pe/pathogen.vim'],
                      mkdir=['~/.vim/autoload'.replace('~', HOME), '~/.vim/bundle'.replace('~', HOME)])
    install_from_git('syntastic', '~/.vim/bundle/syntastic'.replace('~', HOME),
                     ['--depth=1', 'https://github.com/vim-syntastic/syntastic.git'],
                     workdir='~/.vim/bundle'.replace('~', HOME),
                     )
    install_from_git('jedi-vim', '~/.vim/bundle/jedi-vim'.replace('~', HOME),
                     ['--recursive', 'https://github.com/davidhalter/jedi-vim.git'],
                     workdir='~/.vim/bundle'.replace('~', HOME),
                     )
    install_from_curl('monokai', '~/.vim/colors/monokai.vim'.replace('~', HOME),
                      ['-LSso', '~/.vim/colors/monokai.vim'.replace('~', HOME),
                      'https://raw.githubusercontent.com/sickill/vim-monokai/master/colors/monokai.vim'],
                      mkdir=['~/.vim/colors'.replace('~', HOME)])

    print(green('\n{0:^{width}}').format('zsh', width=OUTPUT_WIDTH))
    print(green('=' * OUTPUT_WIDTH))
    install_from_script('oh-my-zsh', '~/.oh-my-zsh'.replace('~', HOME),
                        'https://raw.github.com/robbyrussell/oh-my-zsh/master/tools/install.sh')
    install_from_git('k', '~/.oh-my-zsh/custom/plugins/k'.replace('~', HOME),
                     ['https://github.com/supercrabtree/k'],
                     workdir='~/.oh-my-zsh/custom/plugins'.replace('~', HOME))
    install_from_git('syntax highlight', '~/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting'.replace('~', HOME),
                     ['https://github.com/zsh-users/zsh-syntax-highlighting.git'],
                     workdir='~/.oh-my-zsh/custom/plugins'.replace('~', HOME))
    install_from_git('autosuggestions', '~/.oh-my-zsh/custom/plugins/zsh-autosuggestions'.replace('~', HOME),
                     ['git://github.com/zsh-users/zsh-autosuggestions'],
                     workdir='~/.oh-my-zsh/custom/plugins'.replace('~', HOME))
    install_from_git('directory history', '~/.oh-my-zsh/custom/plugins/zsh-directory-history'.replace('~', HOME),
                     ['https://github.com/tymm/zsh-directory-history'],
                     workdir='~/.oh-my-zsh/custom/plugins'.replace('~', HOME),
                     sudo_link_after=('~/zsh-directory-history/dirhist'.replace('~', HOME), '/usr/bin'))
    install_from_git('powerlevel9k', '~/.oh-my-zsh/custom/themes/powerlevel9k'.replace('~', HOME),
                     ['https://github.com/bhilburn/powerlevel9k.git'],
                     workdir='~/.oh-my-zsh/custom/themes'.replace('~', HOME))

    print(green('\n{0:^{width}}').format('symlinking dotfiles', width=OUTPUT_WIDTH))
    print(green('=' * OUTPUT_WIDTH))


if __name__ == '__main__':
    main()
