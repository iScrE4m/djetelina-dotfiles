current_dir=$(pwd)
script_dir=$(dirname $0)

if [ $script_dir = '.' ]
then
        script_dir="$current_dir"
fi

home_files=(.zshrc .bash_aliases .zsh_aliases .vimrc)

for dotfile in home_files
do
		ln -sf $script_dir/$dotfile ~/dotfile
done
