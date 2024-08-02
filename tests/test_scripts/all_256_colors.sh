#!/bin/bash
for color in $(seq 0 255)
do
    printf '\e[38;5;%dm%3d\e[0m \e[48;5;%dm%3d\e[0m\n' $color $color $color $color
done
