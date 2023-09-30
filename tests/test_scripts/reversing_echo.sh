#!/bin/bash
while true
do
    read INPUT
    echo -e "\e[93m\e[41m$(echo $INPUT | rev)\e[39m\e[49m"
done
