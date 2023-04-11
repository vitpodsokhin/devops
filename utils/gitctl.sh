#!/usr/bin/env bash
#TODO implement `git ls-remote --size <repository_url>` before doing anything! )

print_usage() {
    printf "Usage: %s [directory1] [directory2] ...\n\n" "$0"
    printf "Update all Git repositories in the specified directories and their subdirectories.\n"
    printf "If no directories are specified, search for Git repositories in the current working directory and its subdirectories.\n\n"
    printf "Options:\n"
    printf "  --help  Show this help message and exit\n"
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
    if git -C "$1" rev-parse &>/dev/null; then
        return 0
    else
        printf "Error: %s is not a Git repository\n" "$1"
        return 1
    fi
}

find_repos() {
    repos=$(find "$directories" -type d -exec test -d '{}/.git' ';' -print)

    if [[ -z $repos ]]; then
        printf "No Git repositories found\n"
        exit 0
    fi

    printf "Found Git repositories:\n%s\n" "$repos"
}

confirm_and_update() {
    read -r -p "Update the above Git repositories? [y/N] " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        for repo in $repos; do
            if is_git_repo "$repo"; then
                printf "Updating %s ...\n" "$repo"
                if ! git -C "$repo" pull; then
                    printf "Error updating %s\n" "$repo"
                fi
            fi
        done
        printf "All Git repositories updated successfully\n"
    else
        printf "Aborting update\n"
        exit 0
    fi
}

main() {
    parse_args "$@"
    find_repos && confirm_and_update
}

main "$@"
