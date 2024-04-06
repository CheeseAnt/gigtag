#!/usr/bin/env bash
set -e
set -u
set -o pipefail
 
domain="gigtag"
token="f7132ed4-af6c-4219-8abb-80e595896799"
 
case "$1" in
    "deploy_challenge")
        curl "https://www.duckdns.org/update?domains=$domain&token=$token&txt=$4"
        echo
        ;;
    "clean_challenge")
        curl "https://www.duckdns.org/update?domains=$domain&token=$token&txt=removed&clear=true"
        echo
        ;;
    "deploy_cert")
        # sudo systemctl restart home-assistant@homeassistant.service
        ;;
    "unchanged_cert")
        ;;
    "startup_hook")
        ;;
    "exit_hook")
        ;;
    *)
        echo Unknown hook "${1}"
        exit 0
        ;;
esac
