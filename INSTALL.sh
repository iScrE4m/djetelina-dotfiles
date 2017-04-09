#!/bin/bash

####################
# HELPER VARIABLES #
####################
# Find out where install is located - source directory for everything we need
current_dir=$(pwd)
script_dir=$(dirname "$0")
if [ "$script_dir" = '.' ]; then script_dir="$current_dir"; fi

# Colors
CLEAR='\033[0m'
GREEN='\033[00;32m'
LIGHTGRAY='\033[00;37m'
BLUE='\033[00;34m'
# RED='\033[0;31m'

header_number=0

# If ran as root in docker
if [ "$EUID" -eq 0 ] && [ $(dpkg-query -W -f='${Status}' sudo 2>/dev/null | grep -c "ok installed" ) -eq 0 ]; then
    apt-get install sudo
fi

####################
# HELPER FUNCTIONS #
####################
function greydot() {
    printf "${LIGHTGRAY}.${CLEAR}"
}

function ok_installed() {
    printf "\n${GREEN}%s has been installed${CLEAR}\n" "$1"
}

function header() {
    ((header_number++))
    printf "${BLUE}%s) ${GREEN}%s${BLUE}:${CLEAR} " "$header_number" "$1"
}

function checks_done() {
    printf " ${GREEN}done!${CLEAR}\n"
}

if [ "$1" != "postpull" ]; then
    printf "${BLUE}Fetching latest changes${CLEAR}\n"
    cd "$script_dir" && git pull -q
    "$script_dir"/INSTALL postpull
    exit 0
fi

########################
# INSTALL NEEDED STUFF #
########################
printf "${BLUE}\nChecking and installing dependencies${CLEAR}\n"

# apt section
needed_packages=(python2.7 shellcheck python-pip python3-pip zsh curl vim) 

header "apt"
for package in "${needed_packages[@]}"; do
    if [ $(dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -c "ok installed") -eq 0 ]; then
        printf "\n${BLUE}Apt package ${GREEN}%s${BLUE} is not installed, trying to install (${RED}sudo${BLUE} password may be required)${CLEAR}\n" "$package"
        sudo apt-get install -y "$package"
    else
        greydot
    fi
done
checks_done

# pip install section
# vim sources powerline form 2.7 - todo i guess?
pip2_packages=(powerline-status)
default_pip_packages=(python-jenkins pydocstyle flake8)
pip2 > /dev/null &>2
pip2_status=$?

header "pip"
for package in "${pip2_packages[@]}"; do
    if [ $pip2_status -eq 127 ]; then
        pip -q -q -q install --user --upgrade "${package}"
    else
        pip2 -q -q -q install --user --upgrade "${package}"
    fi
    greydot
done

for package in "${default_pip_packages[@]}"; do
    pip -q -q -q install --user --upgrade "${package}"
    greydot
done
checks_done

# plugins from git
header "git"

## VIM
# pathogen
if [ ! -f "$HOME/.vim/autoload/pathogen.vim" ]; then
    printf "\n${BLUE}pathogen required${CLEAR}\n"
    mkdir -p ~/.vim/autoload ~/.vim/bundle && curl -LSso ~/.vim/autoload/pathogen.vim https://tpo.pe/pathogen.vim
    ok_installed vim-pathogen
else
    greydot
fi

# Syntastic
if [ ! -d "$HOME/.vim/bundle/syntastic" ]; then
    printf "\n${BLUE}syntastic required${CLEAR}\n"
    cd ~/.vim/bundle && git clone --depth=1 https://github.com/vim-syntastic/syntastic.git
    ok_installed syntastic
else
    greydot
fi

# jedi
if [ ! -d "$HOME/.vim/bundle/jedi-vim" ]; then
    printf "\n${BLUE}jedi-vim required${CLEAR}\n"
    cd ~/.vim/bundle/ && git clone --recursive https://github.com/davidhalter/jedi-vim.git
    ok_installed vim-jedi
else
    greydot
fi

# Monokai color scheme
if [ ! -e "$HOME/.vim/colors/monokai.vim" ]; then
    printf "\n${BLUE}vim-monokai required${CLEAR}\n"
    mkdir -p ~/.vim/colors && curl -LSso ~/.vim/colors/monokai.vim https://raw.githubusercontent.com/sickill/vim-monokai/master/colors/monokai.vim
    ok_installed vim-monokai
else
    greydot
fi


## ZSH
# oh-my-zsh
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    printf "\n${BLUE}oh-my-zsh required${CLEAR}\n"
    sh -c "$(curl -fsSL https://raw.github.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"
    ok_installed oh-my-zsh
else
    greydot
fi

# k, better, git-aware version of ls
if [ ! -d "$HOME/.oh-my-zsh/custom/plugins/k" ]; then
    printf "\n${BLUE}k required${CLEAR}\n"
    git clone https://github.com/supercrabtree/k "$HOME/.oh-my-zsh/custom/plugins/k"
    ok_installed k
else
    greydot
fi

# syntax highlighting
if [ ! -d "$HOME/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting" ]; then
    printf "\n${BLUE}zsh-syntax-highlighting required${CLEAR}\n"
    git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "$HOME/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting"
    ok_installed zsh-syntax-highlighting
else
    greydot
fi

# directory history
if [ ! -e "/usr/bin/dirhist" ]; then
    printf "\n${BLUE}zsh-directory-history required${CLEAR}\n"
    git clone https://github.com/tymm/zsh-directory-history "$HOME/zsh-directory-history"
    sudo cp "$HOME/zsh-directory-history/dirhist" /usr/bin
    ok_installed zsh-directory-history
else
    greydot
fi

# powerlevel9k theme
if [ ! -d "$HOME/.oh-my-zsh/custom/themes/powerlevel9k" ]; then
    printf "\n${BLUE}powerlevel9k required${CLEAR}\n"
    git clone https://github.com/bhilburn/powerlevel9k.git ~/.oh-my-zsh/custom/themes/powerlevel9k
    ok_installed powerlevel9k
else
    greydot
fi

checks_done

###########
# UPDATES #
###########

printf "${BLUE}Updating plugins and themes${CLEAR}\n"
header "zsh"
# Find all folders called .git in X and execute this in them:
find "$HOME/.oh-my-zsh" -type d -name .git -exec sh -c "cd \"{}\"/../ && printf \"${LIGHTGRAY}.${CLEAR}\" && git pull -q" \;
find "$HOME/zsh-directory-history" -type d -name .git -exec sh -c "cd \"{}\"/../ && printf \"${LIGHTGRAY}.${CLEAR}\" && git pull -q" \;
checks_done
header "vim"
find "$HOME/.vim" -type d -name .git -exec sh -c "cd \"{}\"/../ && printf \"${LIGHTGRAY}.${CLEAR}\" && git pull -q" \;
checks_done

#####################################
# COPY ALL .FILES TO HOME DIRECTORY #
#####################################
home_files=(zshrc bash_aliases zsh_aliases vimrc)

printf "\n${BLUE}Creating symlinks for dotfiles${CLEAR}\n"
for dotfile in "${home_files[@]}"; do
    ln -sf "$script_dir/$dotfile" "$HOME/.$dotfile"
done

printf "\n${GREEN}All done!${CLEAR}\n"