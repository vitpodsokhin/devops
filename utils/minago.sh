#!/usr/bin/env bash

print_usage() {
    cat <<EOF
  minago.sh - Find files modified in the last N minutes.
  
    Usage: minago.sh [MINUTES] [PATH] [noxdev]
  
      MINUTES - Number of minutes to search for files. Default: 1
      PATH - The directory to search. Default: ./
      noxdev - Do not use -xdev. 
  
    Examples:
      minago.sh 5
      minago.sh noxdev 5
      minago.sh 5 ~/Desktop/
      minago.sh 5 ~/Desktop/ noxdev
EOF
}

parse_args() {
    local minutes=1
    local path="."
    local xdev="-xdev"
    for arg in "$@"; do
        if [[ $arg =~ ^-?[0-9]+$ ]]; then
            minutes=$arg
        elif [[ $arg == "noxdev" ]]; then
            xdev=""
        else
            path=$arg
        fi
    done
    echo "$minutes $path $xdev"
}

find_files() {
    local args=($(parse_args $@))
    find ${args[1]} ${args[2]} -type f -mmin -${args[0]}
}

minago() {
    find_files $@
}

if [[ $1 == "-h" || $1 == "--help" || $1 == "--usage" ]]; then
    print_usage
else
    minago "$@"
fi

