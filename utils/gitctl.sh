#!/usr/bin/env bash

print_usage() {
    cat <<-END
    Usage: $0 [directory1] [directory2] ...
    
    Update all Git repositories in the specified directories and their subdirectories.
    If no directories are specified, search for Git repositories in the current working directory and its subdirectories.
    
    Options:
      --help  Show this help message and exit
END
}

parse_args() {
    if [[ "$1" == "--help" ]]; then
        print_usage
        exit 0
    elif [[ $# -eq 0 ]]; then
        directories="."
    else
        directories="$@"
    fi
}

is_git_repo() {
    git -C "$1" rev-parse &>/dev/null
}

find_repos() {
    repos=$(find $directories -type d -exec test -d '{}/.git' ';' -print)

    if [[ -z $repos ]]; then
        echo "No Git repositories found"
        exit 0
    fi

    echo "Found Git repositories:"
    echo "$repos"
}

confirm_and_update() {
    read -r -p "Update the above Git repositories? [y/N] " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        for repo in $repos; do
            if is_git_repo "$repo"; then
                echo "Updating $repo ..."
                git -C "$repo" pull
            fi
        done
        echo "All Git repositories updated successfully"
    else
        echo "Aborting update"
        exit 0
    fi
}

main() {
    parse_args "$@"
    find_repos && confirm_and_update
}

main "$@"